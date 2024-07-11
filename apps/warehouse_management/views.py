from django.shortcuts import render
from rest_framework import generics, filters, status, permissions
from .models import Store, Warehouse, Category
from .serializers import InventorySerializer, StoreSerializer, WarehouseSerializer, CategorySerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication



