"""
URL configuration for core_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from accounts import views as account_views
from kennel import views as kennel_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chaining/", include("smart_selects.urls")),
    path(
        "login/",
        account_views.login_view,
        name="login",
    ),
    path("", account_views.home_view, name="home"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", account_views.register_view, name="register"),
    path("price_list/", account_views.price_list_view, name="price_list"),

    path("dashboard/", kennel_views.dashboard_view, name="dashboard"),
    path("dashboard/dog/", kennel_views.dashboard_dog_view, name="dashboard_dog"),
    path('dashboard/dog/add/', kennel_views.dog_add_view, name='dog_add'),
    path('dashboard/dog/<uuid:pk>/delete/', kennel_views.dog_delete_view, name='dog_delete'),
    path('dashboard/dog/<uuid:pk>/edit/', kennel_views.dog_edit_view, name='dog_edit'),
    path('dashboard/dog/<uuid:pk>/measurements/', kennel_views.dog_measurements_view, name='dog_measurements'),

    path("dashboard/litter/", kennel_views.dashboard_litter_view, name="dashboard_litter"),
    path('dashboard/litter/add/', kennel_views.litter_add_view, name='litter_add'),
    path('dashboard/litter/<uuid:pk>/delete/', kennel_views.litter_delete_view, name='litter_delete'),
    path('dashboard/litter/<uuid:pk>/edit/', kennel_views.litter_edit_view, name='litter_edit'),

    path("dashboard/puppy/", kennel_views.dashboard_puppy_view, name="dashboard_puppy"),
    path("dashboard/puppy/add/", kennel_views.puppy_add_view, name="puppy_add"),
    path("dashboard/puppy/<uuid:pk>/edit/", kennel_views.puppy_edit_view, name="puppy_edit"),
    path('dashboard/puppy/<uuid:pk>/delete/', kennel_views.puppy_delete_view, name='puppy_delete'),
    path('dashboard/puppy/<uuid:pk>/measurements/', kennel_views.puppy_measurements_view, name='puppy_measurements'),

    path('dashboard/measurement/<uuid:pk>/delete/', kennel_views.measurement_delete_view, name='measurement_delete'),
    path('dashboard/measurement/<uuid:pk>/edit/', kennel_views.measurement_edit_view, name='measurement_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)