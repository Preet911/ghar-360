from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # 👈 root path
    path("login/", views.loginfunc, name="login"),
    # path("signup/selecttype/hello", views.selecttype, name="selecttype"),
    path("signup/", views.signup, name="signup"),
    # path("signup/landlord/", views.landlord_signup, name="landlord_signup"),
    # path("login/tenant/", views.tenant_login, name="tenant_login"),
    # path("login/landlord/", views.landlord_login, name="landlord_login"),
    path("check-username/", views.check_username, name="check_username"),
    path("dashboard/tenant/", views.tenant_dashboard, name="tenant_dashboard"),
    # path("dashboard/landlord/", views.landlord_dashboard, name="landlord_dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("post-property/", views.post_property, name="post_property"),
    path("post-property/form/", views.post_property_form, name="post_property_form"),
    # path("api/cities/", views.api_cities, name="api_cities"),
    # path("api/localities/", views.api_localities, name="api_localities"),
    # path("city-search/", views.city_search, name="city_search"),
    path("locality-search/", views.locality_search, name="locality_search"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path("property/<int:pk>/", views.property_detail, name="property_detail"),
    path("property/<int:pk>/nearby/", views.property_nearby, name="property_nearby"),
    path("search/", views.search_properties, name="search_properties"),
    path("api/property-cities/", views.api_property_cities, name="api_property_cities"),
    path("property/<int:pk>/tenant/", views.property_detail_tenant, name="property_detail_tenant"),
    path("property/<int:pk>/apply/", views.property_apply, name="property_apply"),
    path("applications/", views.my_applications, name="my_applications"),
    path("applications/<int:pk>/accept/", views.application_accept, name="application_accept"),
    path("applications/<int:pk>/reject/", views.application_reject, name="application_reject"),
    path("my-applys/", views.my_applys, name="my_applys"),
    # path("applications/<int:application_pk>/start/", views.start_renting, name="application_start_renting"),
    # path('applications/<int:pk>/start/', views.application_start_renting, name='application_start_renting'),
    path("profile/", views.profile_view, name="profile"),
    path("notifications/", views.notifications_page, name="notifications"),
    path("notifications/pay/<int:pk>/", views.tenant_paid_rent, name="tenant_paid_rent"),
    path("notifications/received/<int:pk>/", views.landlord_received_rent, name="landlord_received_rent"),
    path("stop-renting/<int:rental_id>/", views.stop_renting, name="stop_renting"),
    path("profile/aadhaar-upload/", views.upload_aadhaar, name="aadhaar_upload"),
    path("profile/<int:user_id>/", views.profile_view, name="profile_other"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),


]

