from rest_framework import serializers
from .models import Warehouse, Store, Category


class WarehouseSerializer(serializers.ModelSerializer):
  class Meta:
    model = Warehouse
    fields = "__all__"


class StoreSerializer(serializers.ModelSerializer):
  class Meta:
    model = Store
    fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = "__all__"