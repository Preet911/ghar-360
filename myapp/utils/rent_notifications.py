from datetime import date
from myapp.models import Rental, RentNotification  # replace 'myapp' with your actual app name

def generate_monthly_rent_notifications():
    """
    For each active rental, create a RentNotification for this month if it doesn't already exist.
    This runs once a month or daily via a scheduled job.
    """
    today = date.today()
    rentals = Rental.objects.select_related("tenant", "property__posted_by").all()

    for rental in rentals:
        if not rental.started_at:
            continue

        # Determine due date (same day as started_at)
        start_day = rental.started_at.day
        # Prevent invalid dates for months with <31 days
        this_month_due = date(today.year, today.month, min(start_day, 28))
        landlord = rental.property.posted_by

        # Skip if already created for this month
        already_exists = RentNotification.objects.filter(
            tenant=rental.tenant,
            property_obj=rental.property,
            due_date=this_month_due
        ).exists()

        if not already_exists:
            RentNotification.objects.create(
                tenant=rental.tenant,
                landlord=landlord,
                property_obj=rental.property,
                due_date=this_month_due
            )
            print(f"✅ Created rent notification for {rental.tenant.username} - {rental.property.title}")
