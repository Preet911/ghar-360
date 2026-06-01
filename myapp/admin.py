from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Property
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.contrib import messages
from .models import PoliceVerification, Application, Rental, Property, RentNotification

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = (
        "property",
        "tenant",
        "started_at",
        "application",
    )
    list_filter = (
        "started_at",
    )
    search_fields = (
        "tenant__username",
        "property__title",
    )
    ordering = ("-started_at",)

@admin.register(RentNotification)
class RentNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "property_obj",
        "tenant",
        "landlord",
        "due_date",
        "days_delayed",
        "is_overdue",
        "created_at",
    )
    list_filter = (
        "due_date",
        "created_at",
    )
    search_fields = (
        "tenant__username",
        "landlord__username",
        "property_obj__title",
    )
    readonly_fields = (
        "created_at",
    )
    ordering = ("-created_at",)

@admin.register(PoliceVerification)
class PoliceVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "tenant_fullname", "tenant_phone", "status", "requested_at", "processed_at")
    list_filter = ("status", "requested_at")
    readonly_fields = ("requested_at",)
    actions = ("mark_verified", "mark_unverified")

    def save_model(self, request, obj, form, change):
        """When admin saves a PV and sets status, process immediately."""
        previous_status = None
        if obj.pk:
            previous_status = PoliceVerification.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)

        # If status was changed and now is verified/unverified, enact business rules
        if obj.status and obj.status != previous_status:
            self._process_verification(request, obj)

    def mark_verified(self, request, queryset):
        for obj in queryset:
            obj.status = "verified"
            obj.processed_at = timezone.now()
            obj.save()
            self._process_verification(request, obj)
        self.message_user(request, "Marked selected verifications as VERIFIED.", level=messages.SUCCESS)
    mark_verified.short_description = "Mark selected as VERIFIED"

    def mark_unverified(self, request, queryset):
        for obj in queryset:
            obj.status = "unverified"
            obj.processed_at = timezone.now()
            obj.save()
            self._process_verification(request, obj)
        self.message_user(request, "Marked selected as NOT VERIFIED.", level=messages.SUCCESS)
    mark_unverified.short_description = "Mark selected as NOT VERIFIED"

    def _process_verification(self, request, pv_obj):
        """
        pv_obj.status is either 'verified' or 'unverified'.
        On verified -> create Rental and mark application accepted + property taken.
        On unverified -> set application.status = 'rejected'.
        """
        try:
            app = pv_obj.application
        except Application.DoesNotExist:
            return

        if pv_obj.status == "verified":
            # Only create rental if not already rented and statuses allow
            if not getattr(app.property, "taken", False):
                # create rental and update things atomically
                from django.db import transaction
                with transaction.atomic():
                    # mark application accepted
                    app.status = "accepted"
                    app.save(update_fields=["status"])
                    # mark property taken
                    prop = app.property
                    prop.taken = True
                    prop.save(update_fields=["taken"])
                    # create rental record
                    Rental.objects.create(
                        tenant=app.applicant,
                        property=prop,
                        application=app
                    )
            # update processed timestamp
            pv_obj.processed_at = timezone.now()
            pv_obj.save(update_fields=["processed_at"])
        elif pv_obj.status == "unverified":
            # set application rejected (if not already rejected)
            if app.status != "rejected":
                app.status = "rejected"
                app.save(update_fields=["status"])
            pv_obj.processed_at = timezone.now()
            pv_obj.save(update_fields=["processed_at"])

# Register custom User model with Django's UserAdmin features
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "email","aadhaar_number","aadhaar_image", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("username", "email", "password","aadhaar_number","aadhaar_image")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email","aadhaar_number","aadhaar_image", "password1", "password2", "is_staff", "is_active"),
        }),
    )
    search_fields = ("username", "email")
    ordering = ("username",)

admin.site.register(User, CustomUserAdmin)

# Keep your existing CustomUserAdmin changes if present; register City/Locality/Property:
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "posted_by", "city", "locality", "property_type", "created_at")
    list_filter = ("city", "property_type", "furnish_type")
    search_fields = ("title", "building", "locality__name", "city__name")
