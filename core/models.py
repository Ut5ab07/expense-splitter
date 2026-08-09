from django.db import models

# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="groups_creator"
        )
    members = models.ManyToManyField(
        "auth.User",
        related_name="groups_member"
    )

    def __str__(self):
        return self.name

class Expense(models.Model):
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE,
        related_name="expenses"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2    
    )
    paid_by = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="expenses_paid"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

class ExpenseSplit(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="splits"
    )

    