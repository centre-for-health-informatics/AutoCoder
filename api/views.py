from api import serializers
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

    def post(self, request, format=None, **kwargs):
        doc = request.data
        docFilename = doc["filename"]
        docType = doc["format"]
        docText = doc["content"]
        docSections, docSentences, docTokens, docEntities = self._processDoc(docText)

        return Response(self._makeJSON(docFilename, docSections, docSentences, docTokens, docEntities))

    def _processDoc(self, text):
        """Runs NLP to process document, returns document sections, sentences, tokens, and entities."""
        lp = LanguageProcessor(text)
        sections = lp.getDocumentSections()
        sentences = lp.getDocumentSentences()
        tokens = lp.getDocumentTokens()
        entities = lp.getDocumentEntities()
        return (sections, sentences, tokens, entities)

    def _makeJSON(self, filename, sections, sentences, tokens, entities):
        """Makes a serialized JSON string."""
        obj = {
            "filename": filename,
            "Sections": sections,
            "Sentences": sentences,
            "Tokens": tokens,
            "Entities": entities
        }
        return obj


class UploadAnnotation(APIView):
    """Uploads annotations to backend to be saved."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, **kwargs):

        annotations = request.data.copy()

        self._cleanJSON(annotations)

        newAnnotation, created = Annotation.objects.update_or_create(
            user=request.user,
            sessionId=annotations['sessionId'],
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
        allowed_entity_attr = ['start', 'end', 'type', 'tag']
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


class GetAnnotation(APIView):
    """Request annotations from backend that were previously saved by filename"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, filename, format=None, **kwargs):

        annotations = Annotation.objects.filter(data__name=filename)
        serializer = serializers.AnnotationSerializer(annotations, many=True)
        return Response(serializer.data)


class GetLatestAnnotation(APIView):
    """Request last updated annotation from backend that were previously saved by filename"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, filename, format=None, **kwargs):

        annotations = Annotation.objects.filter(data__name=filename).order_by('-updated')
        if len(annotations) > 0:

            serializer = serializers.AnnotationSerializer(annotations[0], many=False)
            return Response(serializer.data)
        else:
            return Response(status=404)
