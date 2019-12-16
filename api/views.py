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
        docId = doc["id"]
        docType = doc["format"]
        docText = doc["content"]
        docSections, docSentences, docTokens, docEntities = self._processDoc(docText)

        return Response(self._makeJSON(docId, docSections, docSentences, docTokens, docEntities))

    def _processDoc(self, text):
        """Runs NLP to process document, returns document sections, sentences, tokens, and entities."""
        lp = LanguageProcessor(text)
        sections = lp.getDocumentSections()
        sentences = lp.getDocumentSentences()
        tokens = lp.getDocumentTokens()
        entities = lp.getDocumentEntities()
        return (sections, sentences, tokens, entities)

    def _makeJSON(self, id, sections, sentences, tokens, entities):
        """Makes a serialized JSON string."""
        obj = {
            "id": id,
            "sections": sections,
            "sentences": sentences,
            "tokens": tokens,
            "entities": entities
        }
        return obj


class UploadAnnotation(APIView):
    """Uploads annotations to backend to be saved."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, **kwargs):
        annotations = json.loads(request.data['annotations'])
        self._cleanJSON(annotations)

        newAnnotation = Annotation.objects.create(
            user=request.user,
            data=annotations
        )
        newAnnotation.save()
        return HttpResponse(status=200)

    def _cleanJSON(self, annotations):
        # TODO: add some data verification and checks here to prevent exploits

        for annot_type in annotations:
            for annot in annotations[annot_type]:
                if 'color' in annot:
                    del annot['color']


class GetAnnotation(APIView):
    """Request annotations from backend that were previously saved by filename"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, filename, format=None, **kwargs):

        try:
            annotations = Annotation.objects.filter(data__name=filename)
            serializer = serializers.AnnotationSerializer(annotations, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({None})


class GetLatestAnnotation(APIView):
    """Request last updated annotation from backend that were previously saved by filename"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, filename, format=None, **kwargs):

        try:
            annotation = Annotation.objects.filter(data__name=filename).order_by('-updated')[0]
            serializer = serializers.AnnotationSerializer(annotation, many=False)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({None})
