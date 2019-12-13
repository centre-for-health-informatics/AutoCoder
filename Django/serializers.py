from rest_framework import generics, serializers
from django.contrib.auth.models import User, Group


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', "first_name", "last_name")


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name", )


class SocialSerializer(serializers.Serializer):
    """Serializer that accepts OAuth2 access token"""
    access_token = serializers.CharField(allow_blank=False, trim_whitespace=True)
