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


class AnnotationSerializerWithFilename(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()

    def get_filename(self, obj):
        return obj.filename

    class Meta:
        model = Annotation
        fields = ("id", "filename", "updated")