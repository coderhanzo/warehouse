from rest_framework import serializers
from ..warehouse_management.models import Category
from .models import Inventory

class InventorySerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all()
    )

    class Meta:
        model = Inventory
        fields = "__all__"

    def get_categories(self, obj):
        return [category.name for category in obj.categories.all()]
