from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.models import TreeManyToManyField, TreeForeignKey, MPTTModel
from autoslug import AutoSlugField
from ..inventory_management.models import Inventory


class Store(models.Model):
    name = models.CharField(max_length=100)
    assign_inentory = models.ForeignKey(Inventory, on_delete=models.PROTECT, related_name="Inventory")
    description = models.TextField(max_length=450, blank=True)
    location = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)
    location = models.CharField(max_length=100)
    add_store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="Stores"
    )
    description = models.TextField(max_length=450, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(MPTTModel):
    name = models.CharField(max_length=100)
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="Categories"
    )
    parent = TreeForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name