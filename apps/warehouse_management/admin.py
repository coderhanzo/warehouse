from django.contrib import admin
from .models import Warehouse, Store, Category, Inventory
# Register your models here.
admin.site.register(Warehouse)
admin.site.register(Store)
admin.site.register(Category)
admin.site.register(Inventory)