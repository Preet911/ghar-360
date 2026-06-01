# myapp/context_processors.py
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import RentNotification

def pending_notifications(request):
    """
    Returns a single integer 'pending_total' = number of pending notifications
    for the currently logged-in user. Safe for anonymous users.
    """
    if not request.user or not request.user.is_authenticated:
        return {"pending_total": 0}

    # Count tenant notifications where tenant_clicked is False
    tenant_count = RentNotification.objects.filter(
        tenant=request.user, tenant_clicked=False
    ).count()

    # Count landlord notifications where landlord_clicked is False
    landlord_count = RentNotification.objects.filter(
        landlord=request.user, landlord_clicked=False
    ).count()

    return {"pending_total": tenant_count + landlord_count}
