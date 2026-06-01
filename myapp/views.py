from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseBadRequest
from .forms import SignUpForm,LoginForm
from .models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from .forms import PropertyForm
from .models import Property, Application
import requests
import json
from django.shortcuts import render, get_object_or_404
import time
from django.views.decorators.http import require_GET
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Value, IntegerField, Case, When, Sum, F
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
import os
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
import re
import tempfile
import os
import cv2
import numpy as np
from django.conf import settings
from django.contrib.auth import login as auth_login
from .models import RentNotification
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from myapp.models import RentNotification
from django.db.models import Avg, F, Q
from datetime import date
from myapp.models import Rental, RentalHistory

import re, json, hmac, hashlib
import easyocr
import cv2
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
# myapp/views.py
import os
import tempfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from datetime import date as dt_date
from .forms import AadhaarUploadForm
from .models import User
from django.contrib.auth import get_user_model
from .forms import EditProfileForm

@login_required
def edit_profile(request):
    user = request.user  # always editing own profile only

    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("profile")
    else:
        form = EditProfileForm(instance=user)

    return render(request, "edit_profile.html", {"form": form})


# ------------------ start: exact script (do NOT modify) ------------------
import cv2
import easyocr
import re

# Aadhaar Verhoeff checksum
multiplication_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0]
]
permutation_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8]
]

def verhoeff_validate(num):
    c = 0
    for i, item in enumerate(reversed(num)):
        c = multiplication_table[c][permutation_table[(i % 8)][int(item)]]
    return c == 0

def extract_aadhaar(text_all):
    # Step 1: Find any long digit sequence (with/without spaces)
    candidates = re.findall(r"(?:\d\s*){12,16}", text_all)

    for cand in candidates:
        # Remove spaces
        num = re.sub(r"\s+", "", cand)

        # Step 2: Truncate if longer than 12 digits
        if len(num) > 12:
            num = num[:12]

        # Step 3: Only accept 12-digit numbers
        if len(num) == 12 and verhoeff_validate(num):
            return {"aadhaar_number": f"{num[0:4]} {num[4:8]} {num[8:12]}"}

    return {"aadhaar_number": None}
# ------------------ end: exact script ------------------

# single EasyOCR reader instance
_READER = easyocr.Reader(['en'])


@login_required(login_url="login")
def upload_aadhaar(request):
    """
    Handles Aadhaar upload ONLY for the logged-in user.
    After upload, reloads profile page with correct context.
    """

    # The real logged-in user (owner of Aadhaar)
    profile_user = request.user
    is_owner = True

    form = AadhaarUploadForm(request.POST or None, request.FILES or None)
    ocr_raw_text = None
    ocr_result = None

    # Preserve selected year
    try:
        selected_year = int(request.GET.get("year", dt_date.today().year))
    except:
        selected_year = dt_date.today().year

    # -------------------
    # Aadhaar Upload logic
    # -------------------
    if request.method == "POST" and form.is_valid():
        image_file = form.cleaned_data["aadhaar_image"]

        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=os.path.splitext(image_file.name)[1]) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        try:
            results = _READER.readtext(temp_path, detail=0)
            ocr_raw_text = " ".join(results)
            ocr_result = extract_aadhaar(ocr_raw_text)
        except Exception:
            ocr_raw_text = None
            ocr_result = {}
            messages.error(request, "OCR failed — try a clearer image.")

        try:
            os.remove(temp_path)
        except:
            pass

        # Save Aadhaar image
        profile_user.aadhaar_image.save(image_file.name, image_file, save=False)

        # Save Aadhaar number if detected
        if ocr_result and ocr_result.get("aadhaar_number"):
            profile_user.aadhaar_number = ocr_result["aadhaar_number"]
            profile_user.save()
            messages.success(request, f"Aadhaar saved: {ocr_result['aadhaar_number']}")
        else:
            profile_user.save(update_fields=["aadhaar_image"])
            messages.error(request, "Could not extract valid Aadhaar number.")

    # ----------------------
    # Build context (same as profile_view)
    # ----------------------

    rental_history = RentNotification.objects.filter(
        tenant=profile_user,
        due_date__year=selected_year
    ).select_related("property_obj", "property_obj__posted_by").order_by("-due_date")

    all_history = RentNotification.objects.filter(
        tenant=profile_user
    )

    active_rentals = Rental.objects.filter(
        tenant=profile_user
    ).select_related("property__posted_by")

    # ------ Score Calculation ------
    score = 100
    if all_history.exists():
        total_entries = all_history.count()
        total_delayed_days = sum([(r.days_delayed or 0) for r in all_history])
        total_tenant_clicks = sum([1 for r in all_history if r.tenant_clicked])
        total_landlord_clicks = sum([1 for r in all_history if r.landlord_clicked])
        total_timely = sum([1 for r in all_history if (r.days_delayed or 0) == 0])

        penalty = min(total_delayed_days * 0.5, 30)
        penalty += (total_entries - total_tenant_clicks) * 3
        penalty += (total_entries - total_landlord_clicks) * 7

        reward = total_timely * 1.5

        score = max(min(100 - penalty + reward, 100), 0)

    dash_offset = 364 - (364 * score / 100)

    years = [y.year for y in RentNotification.objects.filter(
        tenant=profile_user
    ).dates("due_date", "year")]

    if selected_year not in years:
        years.append(selected_year)

    # --------------------------
    # FINAL CONTEXT (matches profile_view)
    # --------------------------
    context = {
        "profile_user": profile_user,
        "is_owner": True,  # user editing own profile
        "aadhaar_form": form,
        "aadhaar_ocr": ocr_result,
        "raw_text": ocr_raw_text,
        "rental_history": rental_history,
        "active_rentals": active_rentals,
        "score": int(score),
        "dash_offset": dash_offset,
        "selected_year": selected_year,
        "years": sorted(years, reverse=True),
    }

    return render(request, "profile.html", context)


# views.py - adjusted application_accept
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction

@login_required(login_url="login")
@require_POST
def application_accept(request, pk):
    from .models import Application, Property, Rental, PoliceVerification

    app = get_object_or_404(Application, pk=pk)

    # Only property owner can accept
    if app.property.posted_by_id != request.user.id:
        return HttpResponseForbidden("Not allowed")

    # If already taken/rented — block
    if app.property.taken:
        messages.warning(request, "This property is already rented.")
        return redirect(request.META.get("HTTP_REFERER", "/my-listings/"))

    # If application already accepted / rented -> do nothing
    if app.status in ("accepted", "rented"):
        messages.info(request, "Application already accepted.")
        return redirect(request.META.get("HTTP_REFERER", "/my-listings/"))

    # Create or update PoliceVerification row (snapshot tenant/landlord details)
    pv, created = PoliceVerification.objects.get_or_create(application=app, defaults={
        "tenant_aadhaar": getattr(app.applicant, "aadhaar_number", None),
        "tenant_fullname": f"{app.applicant.first_name or ''} {app.applicant.last_name or ''}".strip() or app.applicant.username,
        "tenant_phone": getattr(app.applicant, "mobile", None),
        "landlord_aadhaar": getattr(app.property.posted_by, "aadhaar_number", None),
        "landlord_fullname": f"{app.property.posted_by.first_name or ''} {app.property.posted_by.last_name or ''}".strip() or app.property.posted_by.username,
        "landlord_phone": getattr(app.property.posted_by, "mobile", None),
        "raw_request": {
            "note": "created from landlord accept action",
            "created_by": request.user.id,
        }
    })

    # mark app as waiting verification
    app.status = "verification_pending"
    app.save(update_fields=["status"])

    messages.success(request, f"Application moved to police verification. A superuser will verify shortly.")
    return redirect(request.META.get("HTTP_REFERER", "/my-listings/"))





def some_view(request):
    tenant_pending = 0
    landlord_pending = 0
    if request.user.is_authenticated:
        tenant_pending = RentNotification.objects.filter(
            tenant=request.user, tenant_clicked=False
        ).count()
        landlord_pending = RentNotification.objects.filter(
            landlord=request.user, landlord_clicked=False
        ).count()

    pending_total = tenant_pending + landlord_pending
    return render(request, "base.html", {"pending_total": pending_total})

@login_required(login_url="login")
def notifications_page(request):
    user = request.user

    # Separate notifications for tenants and landlords
    tenant_notifications = RentNotification.objects.filter(tenant=user).select_related("property_obj")
    landlord_notifications = RentNotification.objects.filter(landlord=user).select_related("property_obj")


    # Update delay counters
    for n in tenant_notifications:
        n.update_days_delayed()
    for n in landlord_notifications:
        n.update_days_delayed()

    context = {
        "tenant_notifications": tenant_notifications,
        "landlord_notifications": landlord_notifications,
    }
    return render(request, "notifications.html", context)

@login_required(login_url="login")
def tenant_paid_rent(request, pk):
    notif = get_object_or_404(RentNotification, pk=pk, tenant=request.user)
    notif.tenant_clicked = True
    notif.save(update_fields=["tenant_clicked"])
    return JsonResponse({"success": True, "status": "paid", "id": notif.id})


@login_required(login_url="login")
def landlord_received_rent(request, pk):
    notif = get_object_or_404(RentNotification, pk=pk, landlord=request.user)
    notif.landlord_clicked = True
    notif.save(update_fields=["landlord_clicked"])
    return JsonResponse({"success": True, "status": "received", "id": notif.id})

# # easyocr may be heavy to initialize repeatedly; create a module-level reader if memory allows
# try:
#     import easyocr
#     _EASYOCR_READER = easyocr.Reader(['en'], gpu=False)  # set gpu=True if available
# except Exception as e:
#     _EASYOCR_READER = None
#     # You may want to log this; if None, OCR won't run.

# @login_required(login_url="login")
# @require_POST
# def start_renting(request, application_pk):
#     """
#     Tenant presses "Start Renting" for an accepted application.
#     Preconditions checked:
#       - application exists and belongs to request.user (applicant)
#       - application.status == 'accepted'
#       - property.taken == False
#     Atomically: create Rental, mark property.taken = True, optionally mark application status.
#     """
#     from .models import Application, Rental, Property

#     app = get_object_or_404(Application, pk=application_pk)

#     # must be the applicant
#     if app.applicant_id != request.user.id:
#         return HttpResponseForbidden("You are not allowed to start renting for this application.")

#     # only for accepted apps
#     if app.status != "accepted":
#         messages.error(request, "Only accepted applications can be converted into rentals.")
#         return redirect(request.META.get("HTTP_REFERER", "/"))

#     prop = app.property

#     # if property already taken — block
#     if getattr(prop, "taken", False):
#         messages.error(request, "Property is already marked taken. Cannot start renting.")
#         return redirect(request.META.get("HTTP_REFERER", "/"))

#     # Do atomic operation to avoid races
#     try:
#         with transaction.atomic():
#             # re-fetch property row with SELECT ... FOR UPDATE equivalent
#             prop_for_update = Property.objects.select_for_update().get(pk=prop.pk)

#             if getattr(prop_for_update, "taken", False):
#                 messages.error(request, "Property was just taken by someone else.")
#                 return redirect(request.META.get("HTTP_REFERER", "/"))

#             # create Rental (OneToOne will raise IntegrityError if another rental exists)
#             rental = Rental.objects.create(
#                 tenant=request.user,
#                 property=prop_for_update,
#                 application=app,
#                 started_at=timezone.now(),
#             )

#             # mark property taken
#             prop_for_update.taken = True
#             prop_for_update.save(update_fields=["taken"])

#             # optional: mark application as 'rented' (if you want)
#             app.status = "rented"
#             app.save(update_fields=["status"])

#     except Exception as e:
#         # handle DB-level uniqueness or other issues
#         messages.error(request, f"Could not start renting: {str(e)}")
#         return redirect(request.META.get("HTTP_REFERER", "/"))

    # messages.success(request, f"You started renting '{prop.title}'.")
    # return redirect(request.META.get("HTTP_REFERER", "/"))
    
def stop_renting(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, tenant=request.user)

    # Save to history before deleting
    RentalHistory.objects.create(
        tenant=rental.tenant,
        property_obj=rental.property,
        application=getattr(rental, "application", None),
        started_at=rental.started_at,
        ended_at=date.today()
    )

    rental.delete()
    messages.success(request, "You have successfully stopped renting this property.")
    return redirect("profile")
    
# def profile_view(request):
#     user = request.user
#     selected_year = request.GET.get("year", date.today().year)

#     # Filter rental history (as tenant)
#     rental_history = RentNotification.objects.filter(
#         tenant=user,
#         due_date__year=selected_year
#     ).select_related("property_obj", "property_obj__posted_by")
    
#     all_history = RentNotification.objects.filter(tenant=user)
    
#     active_rentals = Rental.objects.filter(tenant=user).select_related("property__posted_by")

#     # --- Tenant Score Logic ---
#     # Start with 100 points
#     score = 100

#     if all_history.exists():
#         total_entries = all_history.count()
#         total_delayed_days = sum([r.days_delayed or 0 for r in all_history])
#         total_tenant_clicks = sum([1 for r in all_history if r.tenant_clicked])
#         total_landlord_clicks = sum([1 for r in all_history if r.landlord_clicked])
#         total_timely_payments = sum([1 for r in all_history if (r.days_delayed or 0) == 0])

#         # Simple scoring logic:
#         # - Deduct 0.5 point per delayed day (up to 30)
#         # - Deduct 5 points for missing tenant click
#         # - Deduct 5 points for missing landlord click
#         penalty = min(total_delayed_days * (total_delayed_days/10), 30)
#         penalty += (total_entries - total_tenant_clicks) * 3
#         penalty += (total_entries - total_landlord_clicks) * 7
        
#         reward = total_timely_payments * 1.5

#         score = 100 - penalty + reward
#         score = max(min(score, 100), 0)
        
#     else:
#         score = 0  # no history, perfect score
    
#     dash_offset = 364 - (364 * score / 100)

#     # All available years for filter dropdown
#     years = RentNotification.objects.filter(tenant=user).dates("due_date", "year")

#     context = {
#         "user": user,
#         "rental_history": rental_history,
#         "active_rentals": active_rentals,
#         "score": int(score),
#         "dash_offset": dash_offset,
#         "selected_year": int(selected_year),
#         "years": [y.year for y in years],
#     }
#     return render(request, "profile.html", context)



User = get_user_model()

@login_required
def profile_view(request, user_id=None):

    # If user_id passed → landlord is viewing a tenant
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
        is_owner = (profile_user == request.user)
    else:
        profile_user = request.user
        is_owner = True

    selected_year = int(request.GET.get("year", date.today().year))

    rental_history = RentNotification.objects.filter(
        tenant=profile_user,
        due_date__year=selected_year
    ).select_related("property_obj")

    all_history = RentNotification.objects.filter(tenant=profile_user)

    active_rentals = Rental.objects.filter(
        tenant=profile_user
    ).select_related("property__posted_by")

    # -------- SCORE ----------
    score = 100
    if all_history.exists():
        total_entries = all_history.count()
        total_delayed_days = sum([(r.days_delayed or 0) for r in all_history])
        total_tenant_clicks = sum([1 for r in all_history if r.tenant_clicked])
        total_landlord_clicks = sum([1 for r in all_history if r.landlord_clicked])
        total_timely = sum([1 for r in all_history if (r.days_delayed or 0) == 0])

        penalty = min(total_delayed_days * (total_delayed_days/10), 30)
        penalty += (total_entries - total_tenant_clicks) * 3
        penalty += (total_entries - total_landlord_clicks) * 7

        reward = total_timely * 1.5

        score = max(min(100 - penalty + reward, 100), 0)
        
    else:
        score = 0

    dash_offset = 364 - (364 * score / 100)

    years = RentNotification.objects.filter(
        tenant=profile_user
    ).dates("due_date", "year")

    context = {
        "profile_user": profile_user,
        "is_owner": is_owner,
        "rental_history": rental_history,
        "active_rentals": active_rentals,
        "score": int(score),
        "dash_offset": dash_offset,
        "selected_year": selected_year,
        "years": [y.year for y in years],
    }

    return render(request, "profile.html", context)



# put near your other views
@login_required(login_url="login")
def my_applys(request):
    """
    Shows the logged-in user's tenant applications and their statuses.
    """
    # Defensive: import Application lazily in case file organization differs.
    try:
        from .models import Application
    except Exception:
        # If Application doesn't exist, raise 404 to help debug.
        raise Http404("Application model not found. Make sure you have an Application model.")

    apps = Application.objects.filter(applicant=request.user).select_related("property").order_by("-created_at")
    return render(request, "my_applications.html", {"applications": apps})



# @login_required(login_url="login")
# @require_POST
# def application_accept(request, pk):
#     """
#     Accept an application (owner only).
#     """
#     from .models import Application, Property, Rental

#     app = get_object_or_404(Application, pk=pk)

#     # Ensure current user owns the property
#     if app.property.posted_by_id != request.user.id:
#         return HttpResponseForbidden("Not allowed")

#     # If already rented, prevent duplicate acceptance
#     if app.property.taken:
#         messages.warning(request, "This property is already rented.")
#         return redirect(request.META.get("HTTP_REFERER", "/my-listings/"))

#     # Accept this application
#     app.status = "accepted"
#     app.save()

#     # Mark property as taken
#     app.property.taken = True
#     app.property.save()

#     # Reject all other applications for this property
#     Application.objects.filter(property=app.property).exclude(pk=app.pk).update(status="rejected")

#     # Create Rental record
#     Rental.objects.create(
#         tenant=app.applicant,
#         property=app.property,
#         application=app,   # links rental to application
#     )

#     messages.success(request, f"Application from {app.applicant.username} accepted. Rental started.")
#     return redirect(request.META.get("HTTP_REFERER", "/my-listings/"))

@login_required(login_url="login")
@require_POST
def application_reject(request, pk):
    """
    Reject an application (owner only).
    """
    from .models import Application, Property

    app = get_object_or_404(Application, pk=pk)
    if app.property.posted_by_id != request.user.id:
        return HttpResponseForbidden("Not allowed")

    app.status = "rejected"
    app.save()

    messages.success(request, f"Application from {app.applicant.username} rejected.")
    return redirect(request.META.get("HTTP_REFERER", "/my-listings/"))


@login_required(login_url="login")
def my_applications(request):
    """
    Shows all tenant applications for properties owned by the current user.
    """
    # get properties owned by current user
    owned_props = Property.objects.filter(posted_by=request.user).values_list("pk", flat=True)

    # applications for those properties
    applications = Application.objects.filter(property_id__in=owned_props).select_related("applicant", "property")
    
    # Calculate status counts
    pending_count = applications.filter(status='pending').count()
    accepted_count = applications.filter(status='accepted').count()
    rejected_count = applications.filter(status='rejected').count()

    context = {
        "applications": applications,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
    }
    return render(request, "applications.html", context)

# @login_required(login_url="login")
# @require_POST
# def property_apply(request, pk):
#     """
#     POST endpoint to apply for a property.
#     Expects JSON body: {"password": "theUserPassword", "message": "optional"}
#     Returns JSON: {"status":"ok"} or {"status":"error","message":"..."}
#     """
#     user = request.user
#     prop = get_object_or_404(Property, pk=pk)

#     # read password from POST (form-encoded) or JSON
#     password = request.POST.get("password") or (request.body and (json.loads(request.body.decode()).get("password") if request.body else None))
#     message = request.POST.get("message", "") or (request.body and (json.loads(request.body.decode()).get("message", "") if request.body else ""))

#     if not password:
#         return JsonResponse({"status": "error", "message": "Password is required."}, status=400)

#     # verify password
#     if not user.check_password(password):
#         return JsonResponse({"status": "error", "message": "Password incorrect."}, status=403)

#     # Create application (prevent duplicates if you want — optional)
#     # Here we allow multiple applications; to prevent duplicates, you can check for existing Application with same applicant & property.
#     Application.objects.create(property=prop, applicant=user, message=message)

#     return JsonResponse({"status": "ok", "message": "Application submitted."})

import json
from django.utils import timezone

@login_required(login_url="login")
@require_POST
def property_apply(request, pk):
    """
    POST endpoint to apply for a property.
    Expects form-encoded or JSON body:
      - password (required)
      - message (optional)

    Rules enforced:
      - can't apply to your own property (owner)
      - can't apply if there is an existing pending/accepted application by this user for this property
      - can apply if last application was rejected or no previous application
    Returns JSON.
    """
    user = request.user
    prop = get_object_or_404(Property, pk=pk)

    # Don't allow owner to apply
    if prop.posted_by_id == user.id:
        return JsonResponse({"status": "error", "message": "You cannot apply to your own property."}, status=403)

    # Load payload (supports form-encoded or raw JSON)
    data = {}
    # prefer form POST values if present
    if request.POST:
        data["password"] = request.POST.get("password")
        data["message"] = request.POST.get("message", "").strip()
    else:
        try:
            data = json.loads(request.body.decode()) if request.body else {}
        except Exception:
            data = {}

    password = (data.get("password") or "").strip()
    message = data.get("message", "").strip()

    if not password:
        return JsonResponse({"status": "error", "message": "Password is required."}, status=400)

    # verify password
    if not user.check_password(password):
        return JsonResponse({"status": "error", "message": "Password incorrect."}, status=403)

    # check existing active applications
    existing_active = Application.objects.filter(applicant=user, property=prop, status__in=["pending", "accepted"])
    if existing_active.exists():
        return JsonResponse({"status": "error", "message": "You already have an active application for this property."}, status=409)

    # create application (initial status = pending)
    app = Application.objects.create(
        property=prop,
        applicant=user,
        message=message,
        status="pending",
        # if your Application model has created_at auto_now_add, no need to set it
    )

    return JsonResponse({"status": "ok", "message": "Application submitted."})

def api_property_cities(request):
    """
    Return up to 10 distinct city names already present in Property.
    Optional query param:
      - q : typed prefix or substring to filter cities (case-insensitive)
    """
    q = request.GET.get("q", "").strip()
    qs = Property.objects.all()
    if q:
        qs = qs.filter(city__icontains=q)
    # get distinct city strings
    cities = list(qs.values_list("city", flat=True).distinct())
    # normalize (strip), remove empties, sort case-insensitively
    cleaned = sorted({c.strip() for c in cities if c and c.strip()}, key=lambda s: s.lower())
    # return at most 10 suggestions
    return JsonResponse(cleaned[:10], safe=False)

# ---------- Search helper / view ----------
def normalize_tokens(q):
    """Return list of lowercase tokens (alphanumeric only)."""
    if not q:
        return []
    import re
    # split on any non-alphanumeric (keep dot/decimal for '1.5' -> convert later)
    raw_tokens = re.split(r"[^0-9a-zA-Z\.]+", q)
    tokens = [t.lower().strip() for t in raw_tokens if t and t.strip()]
    return tokens

def map_token_to_bhk(token):
    """Try to map common token forms to bhk choice keys used in the model."""
    # model BHK choices: "1rk","1","1.5","2".."15"
    t = token.lower()
    if t in ("1rk", "rk", "1-rk", "1_rk"):
        return "1rk"
    if t in ("1.5", "1_5", "1-5", "1.5bhk"):
        return "1.5"
    # allow tokens like "1bhk", "2bhk", "3bhk"
    import re
    m = re.match(r"^(\d+)(?:bhk)?$", t)
    if m:
        num = m.group(1)
        return num  # "2", "3", ...
    return None

def map_token_to_property_type(token, prop_type_mapping):
    """Return property_type key if token matches one of display names or keys."""
    t = token.lower()
    if t in prop_type_mapping:
        return prop_type_mapping[t]  # direct map (like 'penthouse'->'penthouse')
    return None

def map_token_to_furnish(token, furnish_mapping):
    t = token.lower()
    return furnish_mapping.get(t)

# main view
# def search_properties(request):
#     """
#     GET search endpoint.
#     Query params:
#       - city (required)
#       - q (free text)
#       - bhk (optional explicit)
#       - furnish (optional explicit)
#       - rent_bucket (optional explicit) : an integer - representing bucket*5000 e.g. 0 => 0-4999, 1 => 5000-9999
#       - property_type (optional explicit)
#       - page (optional)
#     """
#     city = request.GET.get("city", "").strip()
#     q = request.GET.get("q", "").strip()
#     explicit_bhk = request.GET.get("bhk", "").strip()
#     explicit_furnish = request.GET.get("furnish", "").strip()
#     explicit_rent_bucket = request.GET.get("rent_bucket", "").strip()
#     explicit_property_type = request.GET.get("property_type", "").strip()

#     # base queryset: only same city (case-insensitive)
#     base_qs = Property.objects.all()
#     if city:
#         base_qs = base_qs.filter(city__iexact=city)
#     else:
#         # if city not provided, show nothing (tenant must choose city)
#         base_qs = Property.objects.none()

#     # prepare mappings for property_type and furnish to help token matching
#     # property_type choices from your model keys -> human labels (duplicate mapping)
#     PROPERTY_TYPE_MAP = {
#         "apartment": "apartment",
#         "independent house": "independent_house",
#         "independent_house": "independent_house",
#         "duplex": "duplex",
#         "independent floor": "independent_floor",
#         "independent_floor": "independent_floor",
#         "villa": "villa",
#         "penthouse": "penthouse",
#         "studio": "studio",
#         "farm house": "farm_house",
#         "farm_house": "farm_house",
#     }
#     # also include singular tokens like "house" -> independent_house
#     PROPERTY_TYPE_SYNONYMS = {
#         "house": "independent_house",
#         "flat": "apartment",
#         "pg": "pg",  # note: property_type choices don't include 'pg' - that's in looking_to
#     }
#     # merge synonyms
#     # build a normalized dict token->key
#     prop_map = {}
#     for k, v in PROPERTY_TYPE_MAP.items():
#         prop_map[k.lower()] = v
#     for k, v in PROPERTY_TYPE_SYNONYMS.items():
#         prop_map[k.lower()] = v

#     FURNISH_MAP = {
#         "fully": "fully",
#         "fully furnished": "fully",
#         "semi": "semi",
#         "semi furnished": "semi",
#         "unfurnished": "unfurnished",
#         "unfurnished": "unfurnished",
#         "semi-furnished": "semi",
#     }

#     # Tokenize free-text
#     tokens = normalize_tokens(q)

#     # derived filters from tokens
#     token_bhk = None
#     token_property_type = None
#     token_furnish = None
#     token_locality_texts = []  # tokens that look like locality (we'll search locality__icontains)
#     other_tokens = []

#     for t in tokens:
#         # try bhk
#         bhk_mapped = map_token_to_bhk(t)
#         if bhk_mapped:
#             token_bhk = bhk_mapped
#             continue
#         # try property type
#         pt = map_token_to_property_type(t, prop_map)
#         if pt:
#             token_property_type = pt
#             continue
#         # try furnish
#         furn = map_token_to_furnish(t, FURNISH_MAP)
#         if furn:
#             token_furnish = furn
#             continue
#         # otherwise treat as general token (title/description/locality)
#         other_tokens.append(t)
#         token_locality_texts.append(t)

#     # combine explicit filters (query parameters) with token-derived ones (explicit overrides token if set)
#     bhk_filter = explicit_bhk or token_bhk
#     furnish_filter = explicit_furnish or token_furnish
#     prop_type_filter = explicit_property_type or token_property_type

#     # rent range mapping - rent_bucket param is integer index each bucket = 5000
#     rent_min = rent_max = None
#     if explicit_rent_bucket:
#         try:
#             bucket = int(explicit_rent_bucket)
#             rent_min = bucket * 5000
#             rent_max = rent_min + 4999
#         except ValueError:
#             rent_min = rent_max = None

#     # Build Q for prioritized matches
#     prioritized_q = Q()

#     # If property_type filter present, add match
#     if prop_type_filter:
#         prioritized_q |= Q(property_type__iexact=prop_type_filter)

#     # If bhk present
#     if bhk_filter:
#         prioritized_q |= Q(bhk__iexact=bhk_filter)

#     # Furnish
#     if furnish_filter:
#         prioritized_q |= Q(furnish_type__iexact=furnish_filter)

#     # Match locality or title/description using other_tokens
#     text_q = Q()
#     for t in other_tokens:
#         text_q |= Q(title__icontains=t) | Q(description__icontains=t) | Q(locality__icontains=t)

#     if text_q:
#         prioritized_q |= text_q

#     # If explicit rent range provided, intersect (i.e. prioritized must also meet rent bucket)
#     if rent_min is not None:
#         prioritized_q &= Q(rent__gte=rent_min, rent__lte=rent_max)

#     # Get prioritized queryset (distinct)
#     if prioritized_q:
#         prioritized_qs = base_qs.filter(prioritized_q).distinct()
#     else:
#         prioritized_qs = base_qs.none()

#     # If explicit filters were set but not matched in tokens, also filter prioritized by them
#     # (already handled by adding to prioritized_q)
#     # Now other properties in same city (not matched)
#     other_qs = base_qs.exclude(pk__in=prioritized_qs.values_list("pk", flat=True))

#     # Pagination (optional) - show 20 per page from merged view if needed
#     # We'll paginate prioritized and others separately or send full lists (simple)
#     page = request.GET.get("page", 1)
#     paginator_prior = Paginator(prioritized_qs, 20)
#     paginator_other = Paginator(other_qs, 20)

#     try:
#         prior_page = paginator_prior.page(page)
#     except:
#         prior_page = paginator_prior.page(1)
#     try:
#         other_page = paginator_other.page(page)
#     except:
#         other_page = paginator_other.page(1)

#     context = {
#         "city": city,
#         "q": q,
#         "filters": {
#             "bhk": bhk_filter,
#             "furnish": furnish_filter,
#             "rent_min": rent_min,
#             "rent_max": rent_max,
#             "property_type": prop_type_filter,
#             "rent_bucket": explicit_rent_bucket,
#         },
#         "prioritized": prior_page,
#         "others": other_page,
#     }
#     return render(request, "search_results.html", context)

# # ---------- helper: geocode a locality string using Nominatim (with retries) ----------
def geocode_locality(locality, max_retries=2, delay_seconds=1):
    """
    Returns (lat, lon) or (None, None) if not found or on failure.
    Retries up to max_retries times after the initial attempt.
    """
    if not locality:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "ghar360-app/1.0 (preetjogani2004@gmail.com)"}
    # headers = {"User-Agent": "ghar360-app/1.0 (your-email@example.com)"}
    params = {"q": locality, "format": "json", "limit": 1, "addressdetails": 0}

    attempts = 0
    while attempts <= max_retries:
        try:
            r = requests.get(url, params=params, headers=headers, timeout=6)
            if r.status_code == 200:
                try:
                    data = r.json()
                except ValueError:
                    data = None
                if data and isinstance(data, list) and len(data) > 0:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return lat, lon
                # valid response but no results → treat as not found
                return None, None
            else:
                # Non-200 (e.g., 429) — retry
                attempts += 1
                time.sleep(delay_seconds)
        except requests.RequestException:
            attempts += 1
            time.sleep(delay_seconds)
    # failed
    return None, None

# def search_properties(request):
#     city = request.GET.get("city", "").strip()
#     q = request.GET.get("q", "").strip()
#     bhk = request.GET.get("bhk")
#     furnish = request.GET.get("furnish")
#     rent_bucket = request.GET.get("rent_bucket")
#     property_type = request.GET.get("property_type")

#     # Base queryset: only this city
#     qs = Property.objects.all()
#     if city:
#         qs = qs.filter(city__iexact=city)

#     # Parse rent bucket
#     rent_min, rent_max = None, None
#     if rent_bucket:
#         try:
#             parts = rent_bucket.split("-")
#             rent_min = int(parts[0])
#             rent_max = int(parts[1])
#         except:
#             pass

#     # Build filters
#     filters = {}
#     if bhk:
#         filters["bhk"] = bhk
#     if furnish:
#         filters["furnish_type"] = furnish
#     if property_type:
#         filters["property_type"] = property_type
#     if rent_min is not None and rent_max is not None:
#         qs = qs.filter(rent__gte=rent_min, rent__lte=rent_max)

#     # Apply filters first
#     filtered_qs = qs.filter(**filters) if filters else qs

#     # Apply search tokens (must match something in title/locality/description/property_type)
#     prioritized = filtered_qs
#     if q:
#         tokens = q.split()
#         token_q = Q()
#         for token in tokens:
#             token_q &= (
#                 Q(title__icontains=token)
#                 | Q(locality__icontains=token)
#                 | Q(description__icontains=token)
#                 | Q(property_type__icontains=token)
#                 | Q(bhk__icontains=token)
#             )
#         prioritized = prioritized.filter(token_q)

#     # Exclude prioritized ones from others
#     other_qs = qs.exclude(pk__in=prioritized.values_list("pk", flat=True))

#     # Optional: pagination
#     prioritized_page = Paginator(prioritized, 12).get_page(request.GET.get("page1"))
#     others_page = Paginator(other_qs, 12).get_page(request.GET.get("page2"))

#     context = {
#         "city": city,
#         "q": q,
#         "filters": {
#             "bhk": bhk,
#             "furnish": furnish,
#             "property_type": property_type,
#             "rent_min": rent_min,
#             "rent_max": rent_max,
#         },
#         "prioritized": prioritized_page,
#         "others": others_page,
#     }
#     return render(request, "search_results.html", context)

# put these imports at top of your views.py (if not already present)
# replace your search_properties with this implementation
# replace your existing search_properties with this
# def search_properties(request):
#     """
#     Search view with scoring for "other" (unstrict) results.

#     Query params:
#       - city (required)
#       - q (free text)
#       - bhk, furnish, rent_bucket, property_type (optional explicit)
#       - page (optional)
#     """
#     city = request.GET.get("city", "").strip()
#     q = request.GET.get("q", "").strip()
#     explicit_bhk = request.GET.get("bhk", "").strip()
#     explicit_furnish = request.GET.get("furnish", "").strip()
#     explicit_rent_bucket = request.GET.get("rent_bucket", "").strip()
#     explicit_property_type = request.GET.get("property_type", "").strip()

#     # -------------------------
#     # IMPORTANT: only show properties that are NOT taken
#     # -------------------------
#     base_qs = Property.objects.filter(taken=False)

#     # scope to city if provided
#     if city:
#         base_qs = base_qs.filter(city__iexact=city)
#     else:
#         base_qs = Property.objects.none()

#     # parse rent bucket -> min/max (each bucket = 5000)
#     rent_min = rent_max = None
#     if explicit_rent_bucket:
#         try:
#             bucket = int(explicit_rent_bucket)
#             rent_min = bucket * 5000
#             rent_max = rent_min + 4999
#         except Exception:
#             rent_min = rent_max = None

#     # tokens list (normalized simple split)
#     tokens = []
#     if q:
#         tokens = [t.strip() for t in q.split() if t.strip()]

#     # --- Build strict criteria (ALL filters AND ALL tokens) ---
#     any_filter_given = False
#     strict_q = Q()

#     # filters go into strict_q as AND
#     if explicit_bhk:
#         strict_q &= Q(bhk__iexact=explicit_bhk)
#         any_filter_given = True
#     if explicit_furnish:
#         strict_q &= Q(furnish_type__iexact=explicit_furnish)
#         any_filter_given = True
#     if explicit_property_type:
#         strict_q &= Q(property_type__iexact=explicit_property_type)
#         any_filter_given = True
#     if rent_min is not None:
#         strict_q &= Q(rent_gte=rent_min, rent_lte=rent_max)
#         any_filter_given = True

#     # tokens: require ALL tokens to be present somewhere (AND across tokens)
#     tokens_strict_q = Q()
#     if tokens:
#         for token in tokens:
#             per_token_q = (
#                 Q(title__icontains=token) |
#                 Q(description__icontains=token) |
#                 Q(locality__icontains=token) |
#                 Q(property_type__icontains=token) |
#                 Q(building__icontains=token) |
#                 Q(bhk__icontains=token)
#             )
#             tokens_strict_q &= per_token_q
#     if tokens:
#         strict_q &= tokens_strict_q

#     # If there is at least some criteria (filters or tokens), compute strict set.
#     if any_filter_given or tokens:
#         prioritized_qs = base_qs.filter(strict_q).distinct()
#     else:
#         prioritized_qs = base_qs.none()

#     # --- Build unstrict Q (union: any filter OR any token) ---
#     unstrict_q = Q()
#     if explicit_bhk:
#         unstrict_q |= Q(bhk__iexact=explicit_bhk)
#     if explicit_furnish:
#         unstrict_q |= Q(furnish_type__iexact=explicit_furnish)
#     if explicit_property_type:
#         unstrict_q |= Q(property_type__iexact=explicit_property_type)
#     if rent_min is not None:
#         unstrict_q |= Q(rent_gte=rent_min, rent_lte=rent_max)

#     if tokens:
#         token_any_q = Q()
#         for token in tokens:
#             token_any_q |= (
#                 Q(title__icontains=token) |
#                 Q(description__icontains=token) |
#                 Q(locality__icontains=token) |
#                 Q(property_type__icontains=token) |
#                 Q(building__icontains=token) |
#                 Q(bhk__icontains=token)
#             )
#         unstrict_q |= token_any_q

#     # --- Annotate scoring for unstrict results ---
#     token_score_expr = None
#     if tokens:
#         token_cases = []
#         for idx, token in enumerate(tokens):
#             match_condition = (
#                 Q(title__icontains=token) |
#                 Q(description__icontains=token) |
#                 Q(locality__icontains=token) |
#                 Q(property_type__icontains=token) |
#                 Q(building__icontains=token) |
#                 Q(bhk__icontains=token)
#             )
#             token_cases.append(
#                 Case(
#                     When(match_condition, then=Value(1)),
#                     default=Value(0),
#                     output_field=IntegerField(),
#                 )
#             )
#         token_score_expr = token_cases[0]
#         for c in token_cases[1:]:
#             token_score_expr = token_score_expr + c
#     else:
#         token_score_expr = Value(0, output_field=IntegerField())

#     filter_parts = []
#     if explicit_bhk:
#         filter_parts.append(Case(When(bhk__iexact=explicit_bhk, then=Value(1)), default=Value(0), output_field=IntegerField()))
#     if explicit_property_type:
#         filter_parts.append(Case(When(property_type__iexact=explicit_property_type, then=Value(1)), default=Value(0), output_field=IntegerField()))
#     if explicit_furnish:
#         filter_parts.append(Case(When(furnish_type__iexact=explicit_furnish, then=Value(1)), default=Value(0), output_field=IntegerField()))
#     if rent_min is not None:
#         filter_parts.append(Case(When(rent_gte=rent_min, rent_lte=rent_max, then=Value(1)), default=Value(0), output_field=IntegerField()))

#     if filter_parts:
#         filter_score_expr = filter_parts[0]
#         for p in filter_parts[1:]:
#             filter_score_expr = filter_score_expr + p
#     else:
#         filter_score_expr = Value(0, output_field=IntegerField())

#     total_score_expr = token_score_expr + filter_score_expr

#     # Now get unstrict queryset annotated with score, exclude strict items
#     if unstrict_q:
#         raw_unstrict_qs = base_qs.filter(unstrict_q).exclude(pk__in=prioritized_qs.values_list("pk", flat=True)).distinct()

#         unstrict_qs = raw_unstrict_qs.annotate(
#             token_score=token_score_expr,
#             filter_score=filter_score_expr,
#             score=total_score_expr
#         ).order_by(F('score').desc(nulls_last=True), '-created_at')
#     else:
#         unstrict_qs = base_qs.none()

#     # Remaining properties (not in strict or unstrict)
#     remaining_qs = base_qs.exclude(pk__in=prioritized_qs.values_list("pk", flat=True)).exclude(pk__in=unstrict_qs.values_list("pk", flat=True))

#     # --- Pagination & packaging ---
#     page = int(request.GET.get("page", 1) or 1)
#     page_size = 20

#     paginator_prior = Paginator(prioritized_qs, page_size)
#     try:
#         prior_page = paginator_prior.page(page)
#     except:
#         prior_page = paginator_prior.page(1)

#     max_fetch = page * page_size
#     unstrict_list = list(unstrict_qs[:max_fetch])
#     remaining_list = list(remaining_qs.order_by('-created_at')[:max_fetch])
#     combined_others = unstrict_list + remaining_list
#     start_idx = (page - 1) * page_size
#     end_idx = start_idx + page_size
#     page_slice = combined_others[start_idx:end_idx]

#     class SimplePage:
#         def __init__(self, items, number, per_page, total_estimate=None):
#             self.object_list = items
#             self.number = number
#             self.paginator = type("P", (), {"per_page": per_page})
#             self.total_estimate = total_estimate

#     others_page = SimplePage(page_slice, page, page_size, total_estimate=len(unstrict_list) + len(remaining_list))

#     context = {
#         "city": city,
#         "q": q,
#         "filters": {
#             "bhk": explicit_bhk or None,
#             "furnish": explicit_furnish or None,
#             "property_type": explicit_property_type or None,
#             "rent_min": rent_min,
#             "rent_max": rent_max,
#             "rent_bucket": explicit_rent_bucket or None,
#         },
#         "prioritized": prior_page,
#         "others": others_page,
#     }
#     return render(request, "search_results.html", context)

def search_properties(request):
    """
    Search view with scoring for "other" (unstrict) results.

    Query params:
      - city (required)
      - q (free text)
      - bhk, furnish, rent_bucket, property_type (optional explicit)
      - page (optional)
    """
    city = request.GET.get("city", "").strip()
    q = request.GET.get("q", "").strip()
    explicit_bhk = request.GET.get("bhk", "").strip()
    explicit_furnish = request.GET.get("furnish", "").strip()
    explicit_rent_bucket = request.GET.get("rent_bucket", "").strip()
    explicit_property_type = request.GET.get("property_type", "").strip()

    # base queryset scoped to city
    base_qs = Property.objects.filter(taken=False)
    if city:
        base_qs = base_qs.filter(city__iexact=city)
    else:
        base_qs = Property.objects.none()

    # parse rent bucket -> min/max (each bucket = 5000)
    rent_min = rent_max = None
    if explicit_rent_bucket:
        try:
            bucket = int(explicit_rent_bucket)
            rent_min = bucket * 5000
            rent_max = rent_min + 4999
        except Exception:
            rent_min = rent_max = None

    # tokens list (normalized simple split)
    tokens = []
    if q:
        tokens = [t.strip() for t in q.split() if t.strip()]

    # --- Build strict criteria (ALL filters AND ALL tokens) ---
    any_filter_given = False
    strict_q = Q()

    # filters go into strict_q as AND
    if explicit_bhk:
        strict_q &= Q(bhk__iexact=explicit_bhk)
        any_filter_given = True
    if explicit_furnish:
        strict_q &= Q(furnish_type__iexact=explicit_furnish)
        any_filter_given = True
    if explicit_property_type:
        strict_q &= Q(property_type__iexact=explicit_property_type)
        any_filter_given = True
    if rent_min is not None:
        strict_q &= Q(rent__gte=rent_min, rent__lte=rent_max)
        any_filter_given = True

    # tokens: require ALL tokens to be present somewhere (AND across tokens)
    tokens_strict_q = Q()
    if tokens:
        for token in tokens:
            per_token_q = (
                Q(title__icontains=token) |
                Q(description__icontains=token) |
                Q(locality__icontains=token) |
                Q(property_type__icontains=token) |
                Q(building__icontains=token) |
                Q(bhk__icontains=token)
            )
            tokens_strict_q &= per_token_q
    if tokens:
        strict_q &= tokens_strict_q

    # If there is at least some criteria (filters or tokens), compute strict set.
    if any_filter_given or tokens:
        prioritized_qs = base_qs.filter(strict_q).distinct()
    else:
        prioritized_qs = base_qs.none()

    # --- Build unstrict Q (union: any filter OR any token) ---
    unstrict_q = Q()
    if explicit_bhk:
        unstrict_q |= Q(bhk__iexact=explicit_bhk)
    if explicit_furnish:
        unstrict_q |= Q(furnish_type__iexact=explicit_furnish)
    if explicit_property_type:
        unstrict_q |= Q(property_type__iexact=explicit_property_type)
    if rent_min is not None:
        unstrict_q |= Q(rent__gte=rent_min, rent__lte=rent_max)

    if tokens:
        token_any_q = Q()
        for token in tokens:
            token_any_q |= (
                Q(title__icontains=token) |
                Q(description__icontains=token) |
                Q(locality__icontains=token) |
                Q(property_type__icontains=token) |
                Q(building__icontains=token) |
                Q(bhk__icontains=token)
            )
        unstrict_q |= token_any_q

    # --- Annotate scoring for unstrict results ---
    # score = token_score + filter_score
    # token_score: count of tokens matched (1 per token per row, regardless of how many fields matched for that token)
    # filter_score: +1 for each explicit filter matched (bhk/type/furnish/rent)
    # We'll build token_score by summing per-token cases (1 if any field contains token)

    token_score_expr = None
    if tokens:
        token_cases = []
        for idx, token in enumerate(tokens):
            # For this token, create a Case When: if any field matches -> 1 else 0
            match_condition = (
                Q(title__icontains=token) |
                Q(description__icontains=token) |
                Q(locality__icontains=token) |
                Q(property_type__icontains=token) |
                Q(building__icontains=token) |
                Q(bhk__icontains=token)
            )
            # Case(When(match_condition, then=1), default=0)
            token_cases.append(
                Case(
                    When(match_condition, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
        # sum all per-token cases
        # start with first expression, then add others using +
        token_score_expr = token_cases[0]
        for c in token_cases[1:]:
            token_score_expr = token_score_expr + c
    else:
        token_score_expr = Value(0, output_field=IntegerField())

    # filter_score_expr: +1 per explicit filter that matches on the row
    filter_parts = []
    if explicit_bhk:
        filter_parts.append(Case(When(bhk__iexact=explicit_bhk, then=Value(1)), default=Value(0), output_field=IntegerField()))
    if explicit_property_type:
        filter_parts.append(Case(When(property_type__iexact=explicit_property_type, then=Value(1)), default=Value(0), output_field=IntegerField()))
    if explicit_furnish:
        filter_parts.append(Case(When(furnish_type__iexact=explicit_furnish, then=Value(1)), default=Value(0), output_field=IntegerField()))
    if rent_min is not None:
        filter_parts.append(Case(When(rent__gte=rent_min, rent__lte=rent_max, then=Value(1)), default=Value(0), output_field=IntegerField()))

    if filter_parts:
        filter_score_expr = filter_parts[0]
        for p in filter_parts[1:]:
            filter_score_expr = filter_score_expr + p
    else:
        filter_score_expr = Value(0, output_field=IntegerField())

    # total score
    total_score_expr = token_score_expr + filter_score_expr

    # Now get unstrict queryset annotated with score, exclude strict items
    if unstrict_q:
        # filter base by unstrict_q and exclude strict
        raw_unstrict_qs = base_qs.filter(unstrict_q).exclude(pk__in=prioritized_qs.values_list("pk", flat=True)).distinct()

        # annotate with score and order by -score, -created_at
        unstrict_qs = raw_unstrict_qs.annotate(
            token_score=token_score_expr,
            filter_score=filter_score_expr,
            score=total_score_expr
        ).order_by(F('score').desc(nulls_last=True), '-created_at')
    else:
        unstrict_qs = base_qs.none()

    # Remaining properties (not in strict or unstrict)
    remaining_qs = base_qs.exclude(pk__in=prioritized_qs.values_list("pk", flat=True)).exclude(pk__in=unstrict_qs.values_list("pk", flat=True))

    # --- Pagination & packaging ---
    page = int(request.GET.get("page", 1) or 1)
    page_size = 20

    # prioritized (strict) pagination
    paginator_prior = Paginator(prioritized_qs, page_size)
    try:
        prior_page = paginator_prior.page(page)
    except:
        prior_page = paginator_prior.page(1)

    # For others: we want unstrict_qs first (ordered by score), then remaining_qs (newest first).
    # We'll fetch enough items to fill the requested page (limit to page*page_size from each source)
    max_fetch = page * page_size
    unstrict_list = list(unstrict_qs[:max_fetch])
    remaining_list = list(remaining_qs.order_by('-created_at')[:max_fetch])
    combined_others = unstrict_list + remaining_list
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_slice = combined_others[start_idx:end_idx]

    class SimplePage:
        def __init__(self, items, number, per_page, total_estimate=None):
            self.object_list = items
            self.number = number
            self.paginator = type("P", (), {"per_page": per_page})
            self.total_estimate = total_estimate

    others_page = SimplePage(page_slice, page, page_size, total_estimate=len(unstrict_list) + len(remaining_list))

    context = {
        "city": city,
        "q": q,
        "filters": {
            "bhk": explicit_bhk or None,
            "furnish": explicit_furnish or None,
            "property_type": explicit_property_type or None,
            "rent_min": rent_min,
            "rent_max": rent_max,
            "rent_bucket": explicit_rent_bucket or None,
        },
        "prioritized": prior_page,
        "others": others_page,
    }
    return render(request, "search_results.html", context)


# ---------- helper: fetch POIs for one category using Overpass (with retries) ----------
def fetch_overpass_pois(lat, lon, radius_m, tags_list, max_retries=2, delay_seconds=1):
    """
    tags_list: e.g. ["amenity=school","amenity=college"]
    Returns list of places (each: dict with name, lat, lon, distance_km, tags).
    """
    if lat is None or lon is None:
        return []

    # build Overpass query parts
    query_parts = []
    for tag in tags_list:
        if "=" not in tag:
            continue
        key, value = tag.split("=", 1)
        query_parts.append(f'node(around:{radius_m},{lat},{lon})[{key}="{value}"];')
        query_parts.append(f'way(around:{radius_m},{lat},{lon})[{key}="{value}"];')
        query_parts.append(f'relation(around:{radius_m},{lat},{lon})[{key}="{value}"];')

    query_text = f"""
[out:json][timeout:25];
(
  {' '.join(query_parts)}
);
out center;
"""

    url = "https://overpass-api.de/api/interpreter"
    attempts = 0
    while attempts <= max_retries:
        try:
            r = requests.get(url, params={"data": query_text}, timeout=25)
            if r.status_code == 200:
                try:
                    data = r.json()
                except ValueError:
                    data = None
                if not data:
                    return []
                elements = data.get("elements", [])
                results = []
                # small local helper to compute distance (haversine)
                import math
                def haversine_km(lat1, lon1, lat2, lon2):
                    R = 6371.0
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = (math.sin(dlat/2) ** 2 +
                         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                         math.sin(dlon/2) ** 2)
                    a = min(1, max(0, a))
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    return R * c

                for el in elements:
                    tags = el.get("tags", {}) or {}
                    name = tags.get("name", "").strip()
                    if not name:
                        continue
                    if "lat" in el and "lon" in el:
                        el_lat, el_lon = el["lat"], el["lon"]
                    else:
                        center = el.get("center")
                        if not center:
                            continue
                        el_lat, el_lon = center.get("lat"), center.get("lon")
                    # compute distance and add
                    distance_km = round(haversine_km(lat, lon, float(el_lat), float(el_lon)), 2)
                    results.append({
                        "name": name,
                        "lat": float(el_lat),
                        "lon": float(el_lon),
                        "distance_km": distance_km,
                        "tags": tags,
                    })
                # sort by distance and return top N (e.g., 5)
                results = sorted(results, key=lambda x: x["distance_km"])
                return results[:5]
            else:
                # server error or rate-limit - retry
                attempts += 1
                time.sleep(delay_seconds)
        except requests.RequestException:
            attempts += 1
            time.sleep(delay_seconds)
    # failed
    return []


# ---------- AJAX endpoint: compute nearby POIs for a property ----------
@login_required(login_url="login")
@require_GET
def property_nearby(request, pk):
    """
    Endpoint: GET /property/<pk>/nearby/
    Returns JSON: {
      "lat": .., "lon": ..,
      "categories": {
         "Education": {"status":"ok","places":[...]} or {"status":"error","message":"..."}
      }
    }
    """
    # get property and ensure it belongs to the user (same permission as property_detail)
    from .models import Property
    prop = get_object_or_404(Property, pk=pk)

    locality = prop.locality or prop.city or ""
    if not locality:
        return JsonResponse({"error": "No locality/city present for this property."}, status=400)

    # STEP A: geocode
    lat, lon = geocode_locality(locality, max_retries=2)
    if lat is None or lon is None:
        # gracefully return no coords (frontend will show message)
        return JsonResponse({
            "lat": None,
            "lon": None,
            "error": "Could not geocode the property locality.",
            "categories": {}
        }, status=200)

    # STEP B: for each category call Overpass (can be tuned)
    search_radius_m = 3000  # you can change this or expose via query param
    categories = {
        "Education": ["amenity=school", "amenity=college", "amenity=university"],
        "Healthcare": ["amenity=hospital", "amenity=clinic", "amenity=pharmacy"],
        "Entertainment": ["amenity=cinema", "amenity=restaurant", "amenity=cafe"],
        "Monumental": ["tourism=attraction", "historic=monument", "leisure=park"],
        "Transport": ["railway=station", "aeroway=aerodrome", "railway=subway_entrance"],
    }

    categories_result = {}
    for cat_name, tags in categories.items():
        try:
            pois = fetch_overpass_pois(lat, lon, search_radius_m, tags, max_retries=2)
            # If empty list, it's fine (no results); not considered an error
            categories_result[cat_name] = {"status": "ok", "places": pois}
        except Exception as e:
            # defensive fallback
            categories_result[cat_name] = {"status": "error", "message": str(e), "places": []}

    return JsonResponse({
        "lat": lat,
        "lon": lon,
        "categories": categories_result
    }, safe=False)

# @login_required(login_url="login")
# def property_detail(request, pk):
#     property_obj = get_object_or_404(Property, pk=pk, posted_by=request.user)
#     images = list(property_obj.images.all()) 
#     return render(request, "property_detail.html", {"property": property_obj})

@login_required(login_url="login")
def property_detail(request, pk):
    # Owner-only detail page (keeps existing owner check)
    prop = get_object_or_404(Property.objects.prefetch_related("images", "posted_by"), pk=pk, posted_by=request.user)
    images = list(prop.images.all())  # prefetched
    return render(request, "property_detail.html", {"property": prop, "images": images})

# @login_required(login_url="login")
# def property_detail_tenant(request, pk):
#     """Tenant-facing property detail page (read-only)."""
#     property_obj = get_object_or_404(Property, pk=pk)

#     # here you can add extra context like lat/lon, POIs, etc. later
#     context = {
#         "property": property_obj,
#     }
#     return render(request, "property_detail_tenant.html", context)

@login_required(login_url="login")
def property_detail_tenant(request, pk):
    """
    Tenant-facing property detail page (read-only).
    Context provided:
      - property : Property instance
      - can_apply : bool (True if Apply button should be active)
      - application_status : None | "pending" | "accepted" | "rejected"
      - last_application : Application instance or None
      - is_owner : True if current user is owner (cannot apply)
    """
    property_obj = get_object_or_404(Property, pk=pk)

    user = request.user
    is_owner = (property_obj.posted_by_id == user.id)

    # Find the most recent application by this user for this property (if any)
    last_app = Application.objects.filter(applicant=user, property=property_obj).order_by("-created_at").first()

    application_status = None
    if last_app:
        application_status = last_app.status  # "pending" / "accepted" / "rejected" etc.

    # Business logic:
    # - If user is owner -> cannot apply
    # - If user has pending or accepted -> cannot apply
    # - If last status is rejected or no application exists -> can apply
    can_apply = True
    if is_owner:
        can_apply = False
    elif application_status in ("pending", "accepted"):
        can_apply = False
    else:
        can_apply = True
        
    images = list(property_obj.images.all()) 

    context = {
        "property": property_obj,
        "is_owner": is_owner,
        "last_application": last_app,
        "application_status": application_status,
        "can_apply": can_apply,
        "images": images,
    }
    return render(request, "property_detail_tenant.html", context)

@login_required(login_url="login")
def my_listings(request):
    properties = Property.objects.filter(posted_by=request.user)
    return render(request, "my_listings.html", {"properties": properties})  

def locality_search(request):
    query = request.GET.get("q", "")
    city = request.GET.get("city", "")

    if not query:
        return JsonResponse([], safe=False)

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{query}, {city}" if city else query,
        "format": "json",
        "addressdetails": 1,
        "limit": 10,
    }
    headers = {
        "User-Agent": "ghar360-app/1.0 (preetjogani2004@gmail.com)"  # ✅ REQUIRED by Nominatim
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)

        # If not valid JSON, return empty list
        try:
            data = r.json()
        except ValueError:
            return JsonResponse([], safe=False)

        return JsonResponse(data, safe=False)

    except requests.RequestException as e:
        print("Locality API error:", e)
        return JsonResponse([], safe=False)


# def locality_search(request):
#     query = request.GET.get("q", "")
#     city = request.GET.get("city", "")

#     if not query:
#         return JsonResponse([], safe=False)

#     url = "https://nominatim.openstreetmap.org/search"
#     params = {
#         "q": f"{query}, {city}" if city else query,
#         "format": "json",
#         "addressdetails": 1,
#         "limit": 10,
#     }
#     headers = {
#         "User-Agent": "YourAppName/1.0 (your_email@example.com)"  # OSM requires this
#     }

#     r = requests.get(url, params=params, headers=headers)
#     return JsonResponse(r.json(), safe=False)

@login_required(login_url="login")
def post_property(request):
    user = request.user

    # Step 1: If user has no listings yet → show "be landlord" page
    if user.no_of_listings == 0:
        if request.method == "POST":  
            # User clicked "Become a Landlord"
            return redirect("post_property_form")  # redirect to form
        return render(request, "be_landlord.html")

    # Step 2: If user already has listings → go directly to form
    return redirect("post_property_form")

# @login_required(login_url="login")
# def post_property_form(request):
#     user = request.user

#     if request.method == "POST":
#         form = PropertyForm(request.POST)
#         if form.is_valid():
#             property = form.save(commit=False)
#             property.posted_by = user
#             property.save()
#             user.no_of_listings += 1   # ✅ increment count
#             user.save()
#             return redirect("home")
#     else:
#         form = PropertyForm()

#     return render(request, "post_property.html", {"form": form})
# @login_required(login_url="login")
# def post_property_form(request):
#     user = request.user

#     if request.method == "POST":
#         form = PropertyForm(request.POST)
#         if form.is_valid():
#             prop = form.save(commit=False)
#             prop.posted_by = user
#             prop.save()
#             user.no_of_listings += 1
#             user.save()
#             return redirect("home")
#         else:
#             # TEMP debug: print errors to console and keep rendering form
#             print("PROPERTY FORM INVALID:", form.errors)
#             # also print non-field errors
#             print("NON-FIELD ERRORS:", form.non_field_errors())
#     else:
#         form = PropertyForm()

#     return render(request, "post_property.html", {"form": form})

import os
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import PropertyForm
from .models import PropertyImage

@login_required(login_url="login")
def post_property_form(request):
    user = request.user

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)  # ✅ important for file upload
        if form.is_valid():
            prop = form.save(commit=False)
            prop.posted_by = user
            prop.save()

            # ---------- IMAGE HANDLING ----------
            files = request.FILES.getlist("images")  # matches <input name="images">
            max_images = 10
            allowed_letters = "abcdefghij"

            files = files[:max_images]
            for idx, f in enumerate(files):
                letter = allowed_letters[idx]
                _, ext = os.path.splitext(f.name)
                ext = ext.lower() or ".jpg"
                filename = f"{prop.pk}({letter}){ext}"

                # ✅ save with custom filename under properties/
                image_obj = PropertyImage(property=prop)
                image_obj.image.save(filename, f, save=True)

            user.no_of_listings += 1
            user.save()
            return redirect("home")
        else:
            print("PROPERTY FORM INVALID:", form.errors)
            print("NON-FIELD ERRORS:", form.non_field_errors())
    else:
        form = PropertyForm()

    return render(request, "post_property.html", {"form": form})


# def api_cities(request):
#     qs = City.objects.all().order_by("name").values("id", "name")
#     return JsonResponse(list(qs), safe=False)


# def api_localities(request):
#     city_id = request.GET.get("city_id")
#     qs = Locality.objects.none()
#     if city_id:
#         qs = Locality.objects.filter(city_id=city_id).order_by("name").values("id", "name")
#     else:
#         qs = Locality.objects.all().order_by("name").values("id", "name")
#     return JsonResponse(list(qs), safe=False)

# @login_required(login_url="login")
# def post_property(request):
#     if request.method == "POST":
#         form = PropertyForm(request.POST)
#         if form.is_valid():
#             property = form.save(commit=False)
#             property.posted_by = request.user
#             property.save()
#             return redirect("home")  # Redirect to home after posting
#     else:
#         form = PropertyForm()
#     return render(request, "post_property.html", {"form": form})


def logout_view(request):
    logout(request)  # clears the session
    return redirect("home")  # 👈 back to login page

# def home(request):
#     return render(request, 'home.html')

def home(request):
    app_count = 0
    if request.user.is_authenticated:
        try:
            app_count = Application.objects.filter(applicant=request.user).count()
        except Exception:
            app_count = 0
    return render(request, "home.html", {"application_count": app_count})


@login_required
def tenant_dashboard(request):
    return render(request, "tenant_dashboard.html")

# @login_required
# def landlord_dashboard(request):
#     return render(request, "landlord_dashboard.html")


def home(request):
    return render(request, "home.html")

# ✅ AJAX Username Availability Check
def check_username(request):
    username = request.GET.get("username", None)
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({"available": not exists})


# ✅ Tenant Signup
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")  # make a dashboard page later
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form, "user_type": "Tenant"})



# ✅ Landlord Signup
# def landlord_signup(request):
#     if request.method == "POST":
#         form = LandlordSignUpForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect("landlord_dashboard")
#     else:
#         form = LandlordSignUpForm()
#     return render(request, "signup.html", {"form": form, "user_type": "Landlord"})


# ✅ Tenant Login
@never_cache
def loginfunc(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


# # ✅ Landlord Login
# def landlord_login(request):
#     if request.method == "POST":
#         form = LandlordLoginForm(request, data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             if user.role == "landlord":
#                 login(request, user)
#                 return redirect("landlord_dashboard")
#             else:
#                 return HttpResponse("Invalid role for this login page")
#     else:
#         form = LandlordLoginForm()
#     return render(request, "login.html", {"form": form, "user_type": "Landlord"})