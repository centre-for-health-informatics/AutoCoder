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
from ICD.models import TreeCode

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


class Family(APIView):
    """Returns the family of a code"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsCoder]

    # Get the children of the entered code
    def get_children(self, inCode):
        try:
            childrenCodes = TreeCode.objects.get(code=inCode).children
            childrenCodes = childrenCodes.split(",")
            children = TreeCode.objects.filter(code__in=childrenCodes)
            for child in children:
                if child.children:
                    child.hasChildren = True
                else:
                    child.hasChildren = False
            return children
        except ObjectDoesNotExist:
            return TreeCode.objects.none()

    # Get the siblings of the entered code
    def get_siblings(self, inCode):
        try:
            if(TreeCode.objects.get(code=inCode).parent):
                parent = TreeCode.objects.get(code=inCode).parent
                siblingCodes = TreeCode.objects.get(
                    code=parent).children.split(",")
                siblings = TreeCode.objects.filter(code__in=siblingCodes)
                for sibling in siblings:
                    if sibling.children:
                        sibling.hasChildren = True
                    else:
                        sibling.hasChildren = False
                return siblings
            else:
                siblings = TreeCode.objects.filter(code=inCode)
                for sibling in siblings:
                    if sibling.children:
                        sibling.hasChildren = True
                    else:
                        sibling.hasChildren = False
                return siblings
        except ObjectDoesNotExist:
            return TreeCode.objects.none()

    # Get self of code
    def get_single(self, inCode):
        try:
            selfs = TreeCode.objects.get(code=inCode)
            if selfs.children:
                selfs.hasChildren = True
            else:
                selfs.hasChildren = False
            return selfs
        except ObjectDoesNotExist:
            return None

    # Uses above functions to get family and combine it all
    def get(self, request, inCode, format=None, **kwargs):
        selfs = self.get_single(inCode)
        if selfs == None:
            return Response({'self': None, 'parent': None, 'siblings': None, 'children': None})
        parent = self.get_single(selfs.parent)
        if(parent != None):
            parent.hasChildren = True
            parentSerializer = serializers.TreeCodeSerializer(parent, many=False)
        children = self.get_children(inCode)
        siblings = self.get_siblings(inCode)
        selfSerializer = serializers.TreeCodeSerializer(selfs, many=False)
        siblingSerializer = serializers.TreeCodeSerializer(siblings, many=True)
        childrenSerializer = serializers.TreeCodeSerializer(children, many=True)

        # Sending json
        if parent:
            return Response({'self': selfSerializer.data, 'parent': parentSerializer.data, 'siblings': siblingSerializer.data, 'children': childrenSerializer.data})
        else:
            return Response({'self': selfSerializer.data, 'parent': None, 'siblings': siblingSerializer.data, 'children': childrenSerializer.data})


class ListAncestors(APIView):
    """Lists the ancestors of a code. Used to generate the ancestry chain in the tree"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsCoder]

    def get_object(self, code):
        ancestors = []
        # Keeps adding ancestors until reaching the top, after which the list is returned
        while True:
            try:
                ancestor = TreeCode.objects.get(code=code)
                serializer = serializers.CodeSerializer(ancestor, many=False)
                ancestors.append(serializer)
                code = ancestor.parent
            except ObjectDoesNotExist:
                return ancestors

    def get(self, request, inCode, format=None, **kwargs):
        ancestors = self.get_object(inCode)
        return Response([ancestor.data for ancestor in ancestors])       


class ListMatchingDescriptions(APIView):
    """Used to match text that the user enters in the search box.
    This is so that the user can enter part of the description instead of the code"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsCoder]

    def get_object(self, searchString):
        # Only check if the length of the entered string is greater than or equal to 3
        if len(searchString) < 3:
            return Code.objects.none()
        # Filters and returns
        searchwords = searchString.lower().split(' ')
        queryset = Code.objects.filter(description__icontains=searchwords[0])
        # Filter down set to match remaining words
        if len(searchwords) > 1:
            for searchword in searchwords[1:]:
                queryset = queryset.filter(description__icontains=searchword)
        # return top 15 codes. shortest codes appear first, then secondary sort by the code
        return queryset.order_by(Length('code').asc(), 'code')[:15]

    def get(self, request, searchString, format=None, **kwargs):
        codes = self.get_object(searchString)
        serializer = serializers.CodeSerializer(codes, many=True)
        return Response(serializer.data)


class ListMatchingKeywords(APIView):
    """Used to match keywords that the user enters in the search box.
    This is so that the user can enter a keyword instead of the code"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsCoder]

    def get_object(self, searchString):
        # Only check if the length of the entered string is greater than or equal to 3
        if len(searchString) < 3:
            return Code.objects.none()
        # Get set matching first word
        searchwords = searchString.lower().split(' ')
        queryset = Code.objects.filter(keyword_terms__icontains=searchwords[0])
        # Filter down set to match remaining words
        if len(searchwords) > 1:
            for searchword in searchwords[1:]:
                queryset = queryset.filter(keyword_terms__icontains=searchword)
        # return top 15 codes. shortest codes appear first, then secondary sort by the code
        return queryset.order_by(Length('code').asc(), 'code')[:15]

    def get(self, request, searchString, format=None, **kwargs):
        codes = self.get_object(searchString)
        serializer = serializers.CodeSerializer(codes, many=True)
        return Response(serializer.data)


class ListChildrenOfCode(APIView):
    """Returns the children of a code"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsCoder]

    def get_object(self, inCode):
        try:
            # Takes the children of the code
            childrenCodes = TreeCode.objects.get(code=inCode).children
            # Turns the children into a list
            childrenCodes = childrenCodes.split(",")
            # Obtains the code objects for each object in the list
            children = TreeCode.objects.filter(code__in=childrenCodes)
            return children
        except ObjectDoesNotExist:
            return TreeCode.objects.none()

    def get(self, request, inCode, format=None, **kwargs):
        children = self.get_object(inCode)
        serializer = serializers.CodeSerializer(children, many=True)
        return Response(serializer.data)


class ListCodeAutosuggestions(APIView):
    """Returns codes based upon the text entered"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsCoder]

    def get(self, request, searchString, format=None, **kwargs):
        descMatch = ListMatchingDescriptions()
        keywordMatch = ListMatchingKeywords()
        codeMatch = ListChildrenOfCode()

        # Matches descriptions, keywords, or codes
        matchesDesc = descMatch.get_object(searchString)
        matchesKeyword = keywordMatch.get_object(searchString)
        matchesCode = codeMatch.get_object(searchString)

        serializerDesc = serializers.CodeSerializer(matchesDesc, many=True)
        serializerKeyword = serializers.CodeSerializer(matchesKeyword, many=True)
        serializerCode = serializers.CodeSerializer(matchesCode, many=True)
        return Response({"description matches": serializerDesc.data, "code matches": serializerCode.data, "keyword matches": serializerKeyword.data})