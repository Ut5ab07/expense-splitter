# Expense Splitter

A Django-based web application for creating groups, recording shared
expenses, splitting costs between group members, and calculating who
owes whom.

The project was built as a practical Django project with a focus on
backend logic, database relationships, authentication, templates, and
clean user-facing workflows.

------------------------------------------------------------------------

## Features

### User Authentication

-   User registration
-   Login and logout
-   Django's built-in authentication system
-   Protected group and expense functionality for authenticated users

### Groups

Users can:

-   Create a group
-   Automatically become a member of the group they create
-   View group members
-   Add other users to a group
-   Open a dedicated group detail page

### Expense Management

Users can:

-   Add an expense to a group
-   Enter the expense amount
-   Select the member who paid
-   Select multiple group members who should share the expense
-   Automatically divide the expense equally among selected members
-   Store one `Expense` record for the expense
-   Store separate `ExpenseSplit` records for each participant

### Balance Calculation

For every group, the application calculates each member's net balance.

A positive balance means the member should receive money.

A negative balance means the member owes money.

For example:

``` text
Utsab      +297.75
Ronaldo     -99.25
messi       -99.25
beckham     -99.25
```

### Debt Simplification

The application converts the calculated balances into suggested
settlements.

Example:

``` text
Ronaldo pays Utsab 99.25
messi pays Utsab 99.25
beckham pays Utsab 99.25
```

This avoids displaying every individual expense as a separate repayment.

### User Interface

The project includes styled pages for:

-   Login
-   Registration
-   Group list
-   Group creation
-   Group detail
-   Add member
-   Add expense

The group detail page displays:

-   Members
-   Current balances
-   Suggested settlements
-   Expenses
-   Expense split information

------------------------------------------------------------------------

## How Expense Splitting Works

Suppose four people share an expense:

``` text
Amount = ₹1200

Participants:
- Utsab
- Ronaldo
- Messi
- Beckham
```

The application calculates:

``` text
₹1200 / 4 = ₹300 per person
```

If Utsab paid the full ₹1200:

``` text
Utsab      +₹900
Ronaldo    -₹300
Messi      -₹300
Beckham    -₹300
```

The payer receives credit for the full amount they paid, while their own
share is deducted as part of the split.

The resulting balances are then passed to the debt simplification
function.

------------------------------------------------------------------------

## Balance Calculation

The core calculation is handled by:

``` python
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
```

The logic is:

1.  Start every group member at `0`.
2.  Add the full expense amount to the person who paid.
3.  Subtract each person's share from their balance.
4.  The final value represents what that person should receive or pay.

------------------------------------------------------------------------

## Debt Simplification

The calculated balances are passed to:

``` python
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

        settlement_amount = min(
            creditor_amount,
            debtor_amount
        )

        settlements.append(
            (
                debtor_id,
                creditor_id,
                settlement_amount
            )
        )

        if creditor_amount > settlement_amount:
            creditors.append(
                (
                    creditor_id,
                    creditor_amount - settlement_amount
                )
            )

        if debtor_amount > settlement_amount:
            debtors.append(
                (
                    debtor_id,
                    debtor_amount - settlement_amount
                )
            )

    return settlements
```

The function separates members into:

-   Creditors --- people who should receive money
-   Debtors --- people who owe money

It then matches debtors with creditors until the balances are settled.

------------------------------------------------------------------------

## Data Model

The project uses Django models to represent users, groups, expenses, and
expense splits.

The main relationships are:

``` text
User
 │
 ├── Group membership
 │
 └── Expenses paid by user
        │
        └── ExpenseSplit
              │
              └── User's share
```

### Group

A group represents a collection of users who share expenses.

Important relationships include:

``` text
Group → Members
Group → Expenses
Group → Creator
```

### Expense

An expense belongs to a group and has a user who paid it.

Conceptually:

``` text
Expense
├── group
├── amount
└── paid_by
```

### ExpenseSplit

An `ExpenseSplit` represents one member's share of a specific expense.

Conceptually:

``` text
ExpenseSplit
├── expense
├── user
└── amount_owed
```

For example, one ₹1200 expense shared by four users produces:

``` text
Expense
₹1200 paid by Utsab

ExpenseSplit
├── Utsab      ₹300
├── Ronaldo    ₹300
├── Messi      ₹300
└── Beckham    ₹300
```

This is intentional. One expense can have multiple split records.

------------------------------------------------------------------------

## Project Structure

A simplified project structure is:

``` text
expense_splitter/
│
├── manage.py
│
├── expense_splitter/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── core/
│   ├── migrations/
│   ├── templates/
│   │   ├── groups/
│   │   └── registration/
│   ├── static/
│   │   └── css/
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   └── ...
│
├── db.sqlite3
└── README.md
```

The exact structure can vary depending on how the project is organized
locally.

------------------------------------------------------------------------

## Main Views

### Registration

The registration view uses Django's `UserCreationForm`.

``` python
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            return redirect("login")

    else:
        form = UserCreationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form},
    )
```

### Create Group

When a group is created:

1.  The group name is read from the submitted form.
2.  The authenticated user becomes the creator.
3.  The creator is automatically added as a group member.

``` python
group = Group.objects.create(
    name=group_name,
    created_by=request.user
)

group.members.add(request.user)
```

### Add Expense

The expense workflow is:

``` text
User enters amount
        ↓
Select payer
        ↓
Select group members
        ↓
Validate selected users
        ↓
Calculate equal share
        ↓
Create Expense
        ↓
Create ExpenseSplit records
        ↓
Return to group detail
```

A key design rule is that the `Expense` is created once, while the
`ExpenseSplit` is created once for every selected participant.

------------------------------------------------------------------------

## Validation

The application validates that:

-   The payer belongs to the group.
-   Every selected participant belongs to the group.
-   The expense has valid participants before creating the split
    records.

This prevents users outside the group from being assigned to an expense.

------------------------------------------------------------------------

## Admin Panel

Django Admin is used to inspect and manage database records.

The admin interface can be used to inspect:

-   Users
-   Groups
-   Expenses
-   Expense splits

For an expense split, the admin can show:

``` text
Expense
User
Amount owed
```

This was also useful during development for checking whether one expense
generated the expected number of split records.

------------------------------------------------------------------------

## Technology Stack

### Backend

-   Python
-   Django
-   SQLite during development

### Frontend

-   HTML
-   CSS
-   Django Templates

### Authentication

-   Django Authentication Framework
-   `UserCreationForm`

### Development Tools

-   VS Code
-   Django development server
-   Django shell
-   Django Admin

------------------------------------------------------------------------

## Installation

### 1. Clone the repository

``` bash
git clone <repository-url>
cd expense_splitter
```

### 2. Create a virtual environment

Windows:

``` bash
python -m venv venv
```

Activate it:

``` bash
venv\Scripts\activate
```

Linux/macOS:

``` bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Django

``` bash
pip install django
```

If the project contains a `requirements.txt` file, use:

``` bash
pip install -r requirements.txt
```

### 4. Apply migrations

``` bash
python manage.py migrate
```

### 5. Create an admin user

``` bash
python manage.py createsuperuser
```

Follow the prompts.

### 6. Start the development server

``` bash
python manage.py runserver
```

Open:

``` text
http://127.0.0.1:8000/
```

------------------------------------------------------------------------

## Basic Usage

### Register

Create an account from the registration page.

### Login

Log in using the registered account.

### Create a group

Create a group such as:

``` text
Madrid Trip
```

The logged-in user is automatically added to the group.

### Add members

Add other registered users to the group.

### Add an expense

For example:

``` text
Amount: ₹1200
Paid by: Utsab

Split between:
- Utsab
- Ronaldo
- Messi
- Beckham
```

The application calculates each member's share automatically.

### View the group

The group detail page shows:

-   Members
-   Balances
-   Suggested settlements
-   Expenses

------------------------------------------------------------------------

## Testing the Balance Logic

The calculation functions can be tested through the Django shell.

Start the shell:

``` bash
python manage.py shell
```

Then:

``` python
from core.models import Group
from core.views import calculate_balances, simplify_debts

group = Group.objects.get(name="Madrid Trip")

balances = calculate_balances(group)

print(balances)
```

To display usernames:

``` python
from django.contrib.auth.models import User

for user_id, balance in balances.items():
    user = User.objects.get(id=user_id)
    print(user.username, balance)
```

Then test debt simplification:

``` python
settlements = simplify_debts(balances)

print(settlements)
```

A result such as:

``` text
[
    (4, 1, Decimal('99.25')),
    (3, 1, Decimal('99.25')),
    (2, 1, Decimal('99.25'))
]
```

means users `4`, `3`, and `2` each need to pay user `1` ₹99.25.

------------------------------------------------------------------------

## Important Development Lessons

This project helped practice several important Django concepts:

### Models and Relationships

The project uses:

-   `ForeignKey`
-   `ManyToManyField`
-   Related objects
-   Cascading relationships

### Forms

Django forms are used for authentication and HTML form handling.

### Templates

Django Template Language is used to:

-   Loop through members
-   Display balances
-   Display settlements
-   Display expenses
-   Generate dynamic URLs

### Authentication

The project uses Django's built-in authentication system instead of
implementing password handling manually.

### Database Design

The separation between `Expense` and `ExpenseSplit` is important.

One expense:

``` text
Expense #1
```

can have multiple:

``` text
ExpenseSplit #1
ExpenseSplit #2
ExpenseSplit #3
ExpenseSplit #4
```

This makes the data model flexible and allows the application to
calculate each person's share.

### Debugging

The project also involved debugging:

-   Migration errors
-   Missing database columns
-   Template errors
-   URL errors
-   Authentication redirects
-   Incorrect indentation
-   Incorrect template context variables
-   Duplicate test records
-   Relationship naming issues

------------------------------------------------------------------------

## Future Improvements

Possible improvements include:

-   Unequal expense splitting
-   Percentage-based splitting
-   Custom split amounts
-   Expense descriptions
-   Expense dates
-   Categories such as Food, Travel, and Accommodation
-   Expense editing and deletion
-   Group member removal
-   Better authorization rules
-   Transaction history
-   Settlement confirmation
-   User dashboards
-   Search and filtering
-   PostgreSQL for production
-   REST API using Django REST Framework
-   Automated tests
-   Deployment with a production server
-   Responsive mobile UI
-   Better error messages and form validation

------------------------------------------------------------------------

## Current Project Goal

The main goal of Expense Splitter is to provide a simple way for a group
of people to track shared expenses without manually calculating who owes
whom.

The core workflow is:

``` text
Create Group
     ↓
Add Members
     ↓
Add Expense
     ↓
Split Expense
     ↓
Calculate Balances
     ↓
Simplify Debts
     ↓
Show Suggested Settlements
```

The project combines Django's backend features with database
relationships and practical financial calculation logic to create a
complete web application.
