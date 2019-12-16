from rest_framework import serializers
from users.models import CustomUser
from annotations.models import Annotation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "username")


class AnnotationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Annotation
        fields = ("id", "user", "data", "updated")
