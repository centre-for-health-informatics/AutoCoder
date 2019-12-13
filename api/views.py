from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from django.http import HttpResponse


class IsActive(permissions.BasePermission):
    def has_permission(self, request, view):
        allowedRoles = []
        if request.user.is_active == True:
            return True
        return False


class ValidateToken(APIView, permissions.BasePermission):
    permission_classes = [permissions.IsAuthenticated, IsActive]

    def get(self, request, format=None, **kwargs):
        return HttpResponse(status=200)
