from django.urls import path, include
from .views import (
    create_group, group_list, logout_view,
    register, login_view, group_detail,
    add_member
)

urlpatterns = [
    path("", group_list, name="group_list"),
    path("register/", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("groups/create/", create_group, name="create_group"),
    path("groups/<int:group_id>/", group_detail, name="group_detail"),
    path("groups/<int:group_id>/add_member/", add_member, name="add_member"),
]