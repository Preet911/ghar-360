from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date

class RentalHistory(models.Model):
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rental_history")
    property_obj = models.ForeignKey("Property", on_delete=models.CASCADE)
    application = models.ForeignKey("Application", on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateField()
    ended_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.username} - {self.property_obj.title} (Ended {self.ended_at})"
class RentNotification(models.Model):
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rent_notifications")
    landlord = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_rent_notifications")
    property_obj = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="rent_notifications")  # ✅ renamed
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    days_delayed = models.PositiveIntegerField(default=0)
    tenant_clicked = models.BooleanField(default=False)
    landlord_clicked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rent Notification: {self.property_obj.title} - {self.tenant.username}"

    @property
    def is_overdue(self):
        """Returns True if current date > due_date"""
        from datetime import date
        return date.today() > self.due_date

    # def update_days_delayed(self):
    #     if self.is_overdue:
    #         from datetime import date
    #         delta = (date.today() - self.due_date).days
    #         self.days_delayed = delta
    #         self.save(update_fields=["days_delayed"])
    
    def update_days_delayed(self):
        # ✅ If both have acknowledged, STOP
        if self.tenant_clicked and self.landlord_clicked:
            return

        today = timezone.now().date()

        if today <= self.due_date:
            self.days_delayed = 0
        else:
            self.days_delayed = (today - self.due_date).days

        self.save(update_fields=["days_delayed"])


class Rental(models.Model):
    """
    Record that a tenant (applicant) has started renting a property.
    One property can be rented by only one tenant at a time (enforced in business logic).
    A tenant can rent multiple properties.
    """
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rentals")
    property = models.OneToOneField("Property", on_delete=models.CASCADE, related_name="rental")
    started_at = models.DateTimeField(default=timezone.now)
    # optional: store which application created this rental (nullable)
    application = models.ForeignKey("Application", on_delete=models.SET_NULL, null=True, blank=True, related_name="rental_record")

    class Meta:
        ordering = ("-started_at",)

    def __str__(self):
        return f"Rental: {self.property} -> {self.tenant} ({self.started_at:%Y-%m-%d})"

class PropertyImage(models.Model):
    property = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/")  # actual name saved will be controlled in view
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property_id} - {self.image.name}"


class User(AbstractUser):
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)
    no_of_listings = models.PositiveIntegerField(default=0)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    aadhaar_number = models.CharField(
        max_length=14, unique=True, null=True, blank=True, help_text="XXXX XXXX XXXX"
    )
    aadhaar_image = models.ImageField(upload_to="aadhaars/", null=True, blank=True, help_text="Uploaded Aadhaar image")

    def __str__(self):
        return self.username
    
    
    # aadhaar_number = models.CharField(max_length=14, unique=True, null=True, blank=True,
    #                                   help_text="Aadhaar in format 'XXXX XXXX XXXX'")
    # aadhaar_image = models.ImageField(
    #     upload_to="aadhaars/",  # will be overridden when saving to set custom filename
    #     null=True,
    #     blank=True,
    #     help_text="Uploaded Aadhaar card image"
    # )

class Application(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("verification_pending", "Verification pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    property = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Application by {self.applicant.username} for {self.property.title}"


class Property(models.Model):
    LOOKING_CHOICES = (
        ("rent", "Rent"),
        ("sell", "Sell"),
        ("pg", "PG"),
    )

    PROPERTY_TYPE_CHOICES = (
        ("apartment", "Apartment"),
        ("independent_house", "Independent House"),
        ("duplex", "Duplex"),
        ("independent_floor", "Independent Floor"),
        ("villa", "Villa"),
        ("penthouse", "Penthouse"),
        ("studio", "Studio"),
        ("farm_house", "Farm House"),
    )

    BHK_CHOICES = [
        ("1rk", "1 RK"),
        ("1", "1 BHK"),
        ("1.5", "1.5 BHK"),
    ] + [(str(i), f"{i} BHK") for i in range(2, 16)]

    AREA_UNIT_CHOICES = (
        ("sq_ft", "sq ft"),
        ("sq_yd", "sq yd"),
        ("sq_mt", "sq mt"),
    )

    FURNISH_CHOICES = (
        ("fully", "Fully Furnished"),
        ("semi", "Semi Furnished"),
        ("unfurnished", "Unfurnished"),
    )

    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    rent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    looking_to = models.CharField(max_length=10, choices=LOOKING_CHOICES)
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPE_CHOICES)
    building = models.CharField("Building / Society / Project", max_length=250, blank=True)
    city = models.CharField(max_length=100)
    locality = models.CharField(max_length=500, blank=True, null=True)
    # locality = models.ForeignKey(Locality, on_delete=models.SET_NULL, null=True, blank=True)
    bhk = models.CharField(max_length=6, choices=BHK_CHOICES)
    built_up_area = models.PositiveIntegerField("Built Up Area")
    area_unit = models.CharField(max_length=10, choices=AREA_UNIT_CHOICES)
    furnish_type = models.CharField(max_length=12, choices=FURNISH_CHOICES)
    
    dining_table = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)
    cupboard = models.BooleanField(default=False)
    sofa = models.BooleanField(default=False)
    microwave = models.BooleanField(default=False)
    stove = models.BooleanField(default=False)
    fridge = models.BooleanField(default=False)
    water_purifier = models.BooleanField(default=False)
    gas_pipeline = models.BooleanField(default=False)
    chimney = models.BooleanField(default=False)
    modular_kitchen = models.BooleanField(default=False)

    # --- Furnishings (Integer Counts) ---
    fan = models.IntegerField(default=0)
    light = models.IntegerField(default=0)
    ac = models.IntegerField(default=0)
    wardrobe = models.IntegerField(default=0)
    tv = models.IntegerField(default=0)
    bed = models.IntegerField(default=0)
    geyser = models.IntegerField(default=0)
    
    power_backup = models.BooleanField(default=False)
    swimming_pool = models.BooleanField(default=False)
    gym = models.BooleanField(default=False)
    lift = models.BooleanField(default=False)
    intercom = models.BooleanField(default=False)
    garden = models.BooleanField(default=False)
    sports = models.BooleanField(default=False)
    kids_area = models.BooleanField(default=False)
    CCTV = models.BooleanField(default=False)
    gated_community = models.BooleanField(default=False)
    club_house = models.BooleanField(default=False)
    community_hall = models.BooleanField(default=False)
    regular_water_supply = models.BooleanField(default=False)
    security_guard = models.BooleanField(default=False)
    visitor_parking = models.BooleanField(default=False)
    maintenance_staff = models.BooleanField(default=False)
    housekeeping = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    
    taken = models.BooleanField(default=False)

    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
    
class PoliceVerification(models.Model):
    STATUS_CHOICES = (
        ("verified", "Verified"),
        ("unverified", "Not verified"),
    )
    # link to application (one-to-one so each application has at most one verification row)
    application = models.OneToOneField(
        "Application",
        on_delete=models.CASCADE,
        related_name="police_verification",
    )

    # raw fields copied for admin inspection (save snapshot when created)
    tenant_aadhaar = models.CharField(max_length=20, null=True, blank=True)
    tenant_fullname = models.CharField(max_length=200, null=True, blank=True)
    tenant_phone = models.CharField(max_length=20, null=True, blank=True)

    landlord_aadhaar = models.CharField(max_length=20, null=True, blank=True)
    landlord_fullname = models.CharField(max_length=200, null=True, blank=True)
    landlord_phone = models.CharField(max_length=20, null=True, blank=True)

    # status is NULL initially; admin sets either 'verified' or 'unverified'
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, null=True, blank=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    raw_request = models.JSONField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("-requested_at",)

    def __str__(self):
        return f"PoliceVerification(app={self.application_id}, status={self.status})"
