from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from .models import Expense, Group, ExpenseSplit
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal

import logging
logger = logging.getLogger(__name__)

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save()

                logger.info(
                    "New user registered: %s",
                    user.username,
                )

                return redirect("login")

            except Exception:
                logger.exception(
                    "Unexpected error during user registration."
                )

        else:
            logger.warning(
                "Registration failed due to invalid form data."
            )

    else:
        form = UserCreationForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form,
        },
    )
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(
            request,
            username=username,
            password=password
        )
        if user is not None:
            login(request,user)
            return redirect("login")

        return render(
            request,
            "registration/login.html",
            {
                "error": "Invalid username or password."
            },
        )

    return render(
        request,
        "registration/login.html"
    )

def logout_view(request):
    logout(request)
    return redirect("home")

def create_group(request):
    if request.method == "POST":
        group_name = request.POST.get("group_name")
        group = Group.objects.create(
            name=group_name,
            created_by= request.user
        )
        group.members.add(request.user)

        return redirect("group_list")

    return render(request, "groups/create.html")

def group_list(request):
    groups = Group.objects.filter(members=request.user)
    return render(
        request,
        "groups/list.html",
        {
            "groups":groups
        }
    )

def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    return render(request, "groups/detail.html",{
        "group": group
    })

def add_member(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.user != group.created_by:
        return HttpResponseForbidden("You are not allowed to add members.")

    if request.method == "POST":
        username = request.POST.get("username")
        try:
            user = User.objects.get(username=username)
            group.members.add(user)
            return redirect("group_detail", group_id=group.id)
        except User.DoesNotExist:
            return render(request, "groups/detail.html", {
                "group": group,
                "error": "User does not exist."
            })

    return render(request, "groups/add_member.html", {
        "group": group
    })

def add_expense(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    members = group.members.all()

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))

        paid_by = get_object_or_404(
            User,
            id=request.POST.get("paid_by")
        )

        split_between = request.POST.getlist("split_between")
        print("Selected users:", split_between)

        split_users = []

        # Make sure the person who paid is a group member
        if not group.members.filter(id=paid_by.id).exists():
            return HttpResponse(
                f"{paid_by.username} is not a member of this group.",
                status=400
            )

        # Validate all selected users
        for user_id in split_between:
            user = get_object_or_404(User, id=user_id)

            if not group.members.filter(id=user.id).exists():
                return HttpResponse(
                    f"{user.username} is not a member of this group.",
                    status=400
                )

            split_users.append(user)

        print("Split users:", [user.username for user in split_users])

        # Calculate equal share
        share = amount / len(split_users)

        # Create the expense
        expense = Expense.objects.create(
            group=group,
            amount=amount,
            paid_by=paid_by,
        )

        # Create a split for every selected user
        for user in split_users:
            ExpenseSplit.objects.create(
                expense=expense,
                user=user,
                amount_owed=share
            )

        return redirect("group_detail", group_id=group.id)

    return render(
        request,
        "groups/add_expense.html",
        {
            "group": group,
            "members": members
        }
    )

def calculate_balances(group):
    balances = {}

    for member in group.members.all():
        balances[member.id] = Decimal(0)

    expenses = Expense.objects.filter(group=group)

    for expense in expenses:
        paid_by = expense.paid_by
        balances[paid_by.id] += expense.amount

        splits = ExpenseSplit.objects.filter(expense=expense)

        for split in splits:
            user = split.user   
            balances[user.id] -= split.amount_owed

    return balances
    

def simplify_debts(balances):
    creditors = []
    debtors = []

    for user_id, balance in balances.items():
        if balance > 0:
            creditors.append((user_id, balance))
        elif balance < 0:
            debtors.append((user_id, -balance))

    settlements = []

    while creditors and debtors:
        creditor_id, creditor_amount = creditors.pop()
        debtor_id, debtor_amount = debtors.pop()

        settlement_amount = min(creditor_amount, debtor_amount)

        settlements.append((debtor_id, creditor_id, settlement_amount))

        if creditor_amount > settlement_amount:
            creditors.append((creditor_id, creditor_amount - settlement_amount))
        if debtor_amount > settlement_amount:
            debtors.append((debtor_id, debtor_amount - settlement_amount))

    return settlements

