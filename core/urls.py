from django.urls import path, include
from .views import (
    create_group, group_list, logout_view, register, login_view
)

urlpatterns = [
    path("", group_list, name="group_list"),
    path("register/", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("groups/create/", create_group, name="create_group"),
]