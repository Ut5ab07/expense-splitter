"""
URL configuration for expense_splitter project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.urls import include, path

from core.views import (
    add_expense, add_member, create_group, group_detail, group_list, logout_view, register
)
from django.contrib.auth.views import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("groups/", group_list, name="group_list"),

    path("register/", register, name="register"),
    path("login/", LoginView.as_view(
        template_name="registration/login.html"
    ), name="login"),
    path("logout/", logout_view, name="logout"),

    path("groups/create/", create_group, name="create_group"),
    path("groups/<int:group_id>/", group_detail, name="group_detail"),
    path("groups/<int:group_id>/add_member/", add_member, name="add_member"),
    path("groups/<int:group_id>/add_expense/", add_expense, name="add_expense"),
]
