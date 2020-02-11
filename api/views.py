from api import serializers, pagination
from rest_framework import generics
from rest_framework.views import APIView
from django.http import Http404
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404
from django.db.models.functions import Length
from itertools import combinations
from django.http import HttpResponse
from django.forms.models import model_to_dict
import json
from django.db.models import Q
from django.db import transaction
from users.models import CustomUser
from django.contrib.auth.hashers import make_password
from annotations.models import Annotation
from NLP.languageProcessor import LanguageProcessor
from django.contrib.postgres.fields.jsonb import KeyTextTransform, KeyTransform
import os

ENABLE_LANGUAGE_PROCESSOR = os.environ['DJANGO_ENABLE_LANGUAGE_PROCESSOR'].lower() == "true"


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        allowedRoles = []
        if request.user.role == "admin":
            return True
        return False


class IsCoder(permissions.BasePermission):
    def has_permission(self, request, view):
        allowedRoles = []
        if request.user.role == "coder":
            return True
        return False


@permission_classes((permissions.AllowAny,))
class CreateUser(APIView):
    """Is used to create a user when receiving information from the sign-up page"""

    def post(self, request, format=None, **kwargs):
        # Takes in all user info
        body = request.data
        fname = body['fname']
        lname = body['lname']
        email = body['email'].lower()
        password = make_password(body['password'])
        username = body['username'].lower()

        # Checks for duplicate username
        try:
            duplicatedUserName = CustomUser.objects.get(username=username)
            return HttpResponse(json.dumps({"message": "Please try a different username."}), status=409)
        except:
            pass

        # Checks for duplicate email
        try:
            duplicatedUserEmail = CustomUser.objects.get(email=email)
            return HttpResponse(json.dumps({"message": "Please try a different email address."}), status=409)

        # Creates user if no errors from previous checks
        except:
            user = CustomUser.objects.create(first_name=fname, last_name=lname,
                                             email=email, password=password, username=username)
            user.save()
            return HttpResponse(json.dumps({"message": "User created."}), status=200)


class RejectUser(APIView):
    """This is used  to remove a user from the system if the admin does not approve their account"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, idToDelete, format=None, **kwargs):
        try:
            # Deleting the user
            user = CustomUser.objects.get(id=idToDelete)
            user.delete()
            return HttpResponse(status=200)
        except ObjectDoesNotExist:
            return HttpResponse(status=400)


class ValidateToken(APIView, permissions.BasePermission):
    """This is used to validate the token"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None, **kwargs):
        return HttpResponse(status=200)


class UploadDoc(APIView):
    """Uploads document for processing"""
    permission_classes = [permissions.IsAuthenticated]
    if ENABLE_LANGUAGE_PROCESSOR:
        langProcessor = LanguageProcessor()

    def post(self, request, format=None, **kwargs):

        doc = request.data
        docFilename = doc["filename"]
        docType = doc["format"]
        docText = doc["content"]

        if ENABLE_LANGUAGE_PROCESSOR:
            docSections, docSentences, docTokens, docEntities = self._processDoc(docText)
            return Response(self._makeJSON(docFilename, docSections, docSentences, docTokens, docEntities))
        else:
            return Response({"filename": docFilename, "Sentences": [], "Tokens": [], "Entities": []})

    def _processDoc(self, text):
        """Runs NLP to process document, returns document sections, sentences, tokens, and entities."""

        results = UploadDoc.langProcessor.analyzeText(text, scope='sentence')

        entities = results['entities']
        sections = results['sections']
        sentences = results['sentences']
        tokens = results['tokens']

        return (sections, sentences, tokens, entities)

    def _makeJSON(self, filename, sections, sentences, tokens, entities):
        """Makes a serialized JSON string."""
        obj = {
            "filename": filename,
            "Sentences": sentences,
            "Tokens": tokens,
            "Entities": entities + sections
        }
        return obj


class UploadAnnotation(APIView):
    """Uploads annotations to backend to be saved."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, **kwargs):
        print(request.data)
        annotations = request.data.copy()

        self._cleanJSON(annotations)

        newAnnotation, created = Annotation.objects.update_or_create(
            user=request.user,
            sessionId=annotations['sessionId'],
            data__name=request.data['name'],
            defaults={
                'user': request.user,
                'sessionId': annotations['sessionId'],
                'data': annotations,
            }
        )

        if created:
            return HttpResponse({'New annotation created'}, status=201)
        else:
            return HttpResponse({'Annotation updated.'}, status=200)

    def _cleanJSON(self, annotations):
        """Cleans the JSON uploaded, remove any unwanted fields"""
        allowed_keys = ['name', 'tagTemplates', 'Sections', 'Entities', 'Sentences', 'sessionId']
        allowed_tagTemplate_attr = ['id', 'description', 'color', 'type']
        allowed_section_attr = ['start', 'end', 'type', 'tag']
        allowed_entity_attr = ['start', 'end', 'type', 'tag', 'next']
        allowed_sentence_attr = ['start', 'end', 'tag']

        # Check the first level keys of the JSON object and delete keys not allowed
        keys_to_remove = []
        keys_in_annotations = []
        for key in annotations:
            if not key in allowed_keys:
                keys_to_remove.append(key)
            else:
                keys_in_annotations.append(key)
        for key in keys_to_remove:
            del annotations[key]

        if 'Sections' in keys_in_annotations:
            self._clean_attributes(annotations, 'Sections', allowed_section_attr)
        if 'tagTemplates' in keys_in_annotations:
            self._clean_attributes(annotations, 'tagTemplates', allowed_tagTemplate_attr)
        if 'Entities' in keys_in_annotations:
            self._clean_attributes(annotations, 'Entities', allowed_entity_attr)
        if 'Sentences' in keys_in_annotations:
            self._clean_attributes(annotations, 'Sentences', allowed_sentence_attr)

    def _clean_attributes(self, annotations, attr, allowed_attr):
        """Given a list of allowed attributes for each object, removes unwanted objects."""
        for item in annotations[attr]:
            attr_to_remove = []
            for attr in item:
                if not attr in allowed_attr:
                    attr_to_remove.append(attr)

            for attr in attr_to_remove:
                del item[attr]


class GetAnnotationsByFilenameUser(APIView):
    """Request annotations from backend that were previously saved by filename"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, filename, format=None, **kwargs):

        annotations = Annotation.objects.filter(data__name=filename).filter(user=request.user)
        serializer = serializers.AnnotationSerializer(annotations, many=True)
        return Response(serializer.data)


class GetAllAnnotationsByCurrentUserWithPagination(APIView):
    """Request all annotations done for all files by the current user"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None, **kwargs):

        orderBy = request.GET['orderBy']

        if request.GET['order'] == 'desc':
            order = '-'
        else:
            order = ''

        # Adding 'filename' field to annotation object by taking the value of 'name' (key) in 'data' (json field)
        annotations = Annotation.objects.filter(user=request.user).annotate(
            filename=KeyTextTransform('name', 'data')).order_by(order + orderBy)
        paginator = pagination.CustomPageNumberPagination()
        results = paginator.paginate_queryset(annotations, request)
        serializer = serializers.AnnotationSerializerWithFilename(results, many=True)
        return paginator.get_paginated_response(serializer.data)


class GetAllAnnotationsWithPagination(APIView):
    """Request all annotations done for all files for admin review"""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request, format=None, **kwargs):

        orderBy = request.GET['orderBy']

        if request.GET['order'] == 'desc':
            order = '-'
        else:
            order = ''

        # Adding 'filename' field to annotation object by taking the value of 'name' (key) in 'data' (json field)
        annotations = Annotation.objects.all().select_related('user').annotate(
            filename=KeyTextTransform('name', 'data')).order_by(order + orderBy)

        paginator = pagination.CustomPageNumberPagination()
        results = paginator.paginate_queryset(annotations, request)
        serializer = serializers.AnnotationSerializerWithFilename(results, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExportAnnotations(APIView):
    """Returns annotations to export based on sessionId"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, sessionId, format=None, **kwargs):
        # filtering annotations from current session for specific user
        annotations = Annotation.objects.filter(user=request.user).filter(sessionId=sessionId)
        # Adding fields to objects based upon json (see GetAllAnnotationsByCurrentUserWithPagination for in depth explantion)
        annotations = annotations.annotate(Entities=KeyTransform('Entities', 'data'))
        annotations = annotations.annotate(Sentences=KeyTransform('Sentences', 'data'))
        annotations = annotations.annotate(tagTemplates=KeyTransform('tagTemplates', 'data'))
        annotations = annotations.annotate(name=KeyTextTransform('name', 'data'))

        serializer = serializers.AnnotationSerializerForExporting(annotations, many=True)
        return Response(serializer.data)


class DownloadAnnotationsById(APIView):
    """Downloads annotations by ID"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id, format=None, **kwargs):
        annotations = Annotation.objects.filter(user=request.user).filter(id=id)
        # Adding fields to objects based upon json (see GetAllAnnotationsByCurrentUserWithPagination for in depth explantion)
        annotations = annotations.annotate(Entities=KeyTransform('Entities', 'data'))
        annotations = annotations.annotate(Sentences=KeyTransform('Sentences', 'data'))
        annotations = annotations.annotate(tagTemplates=KeyTransform('tagTemplates', 'data'))
        annotations = annotations.annotate(name=KeyTextTransform('name', 'data'))

        serializer = serializers.AnnotationSerializerForExporting(annotations, many=True)
        return Response(serializer.data)
