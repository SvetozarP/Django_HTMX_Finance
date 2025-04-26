from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import TransactionQuerySet

class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

# Transaction can be Income or Expense
# Transaction has amount
# has a category(FK)
# tied to user(FK)
# has a DATE
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    type = models.CharField(max_length=7, choices=TRANSACTION_TYPE_CHOICES)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    date = models.DateField()

    objects = TransactionQuerySet.as_manager()

    def __str__(self):
        return f'{self.type} - {self.amount} - {self.date} - {self.user}'

    class Meta:
        ordering = ['-date']