from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.models import TreeForeignKey
from autoslug import AutoSlugField


# Create your models here.
class Inventory(models.Model):
    product_name = models.CharField(
        max_length=100, unique=True
    )  # Will look into wheather creating a product model is needed, if it is then this field can be a foreign key to that model
    # categories = TreeManyToManyField(Category, related_name="Inventory")
    quantity = models.IntegerField()
    location = models.CharField(
        max_length=10, unique=True
    )  # this field will show where the inventory is located in the store
    weight = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name
