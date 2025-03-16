from django.contrib import admin

from tracker.models import Transaction, Category

# Register your models here.

admin.site.register(Transaction)
admin.site.register(Category)