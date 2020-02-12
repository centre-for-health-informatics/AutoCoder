from rest_framework import serializers
from users.models import CustomUser
from annotations.models import Annotation
from annotations.models import TreeCode


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
    user = serializers.SerializerMethodField()

    def get_filename(self, obj):
        return obj.filename

    def get_user(self, obj):
        return obj.user.username

    class Meta:
        model = Annotation
        fields = ("id", "filename", "updated", "user")


class AnnotationSerializerForExporting(serializers.ModelSerializer):
    Entities = serializers.SerializerMethodField()
    Sentences = serializers.SerializerMethodField()
    tagTemplates = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name

    def get_Entities(self, obj):
        return obj.Entities

    def get_Sentences(self, obj):
        return obj.Sentences

    def get_tagTemplates(self, obj):
        return obj.tagTemplates

    class Meta:
        model = Annotation
        fields = ('name', 'Entities', 'Sentences', 'tagTemplates')


class TreeCodeSerializer(serializers.ModelSerializer):
    hasChildren = serializers.SerializerMethodField()

    def get_hasChildren(self, obj):
        return obj.hasChildren

    class Meta:
        model = TreeCode
        fields = ("code", "description", "hasChildren")


class CodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeCode
        fields = ("code", "description")