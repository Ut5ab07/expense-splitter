from django.urls import path, include
from .views import (
    create_group, group_list, logout_view,
    register, login_view, group_detail,
    add_member, add_expense
)
from django.contrib.auth.views import LoginView

urlpatterns = [
    path("", group_list, name="group_list"),
    path("register/", register, name="register"),
    path(
        "login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", logout_view, name="logout"),
    path("groups/create/", create_group, name="create_group"),
    path("groups/<int:group_id>/", group_detail, name="group_detail"),
    path("groups/<int:group_id>/add_member/", add_member, name="add_member"),
    path("groups/<int:group_id>/add_expense/", add_expense, name="add_expense"),
]