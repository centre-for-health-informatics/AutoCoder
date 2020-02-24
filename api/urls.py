from django.urls import path
from api import views

urlpatterns = [
    path('createUser/', views.CreateUser.as_view(), name="create-user"),
    path('validateToken/', views.ValidateToken.as_view(), name="validate-token"),
    path('uploadDoc/', views.UploadDoc.as_view(), name="upload-doc"),
    path('uploadAnnot/', views.UploadAnnotation.as_view(), name="upload-annot"),
    path('getAllMyAnnots/',
         views.GetAllAnnotationsByCurrentUserWithPagination.as_view(), name="get-all-my-annot"),
     path('getAllAnnots/',
         views.GetAllAnnotationsWithPagination.as_view(), name="get-all-annot"),
    path('getAnnotationsByFilenameUser/<str:filename>/',
         views.GetAnnotationsByFilenameUser.as_view(), name="get-annotations-filename-user"),
    path('exportAnnotations/<str:sessionId>/', views.ExportAnnotations.as_view(), name='export-annotations'),
    path('downloadAnnotations/<str:id>/', views.DownloadAnnotationsById.as_view(), name='download-annotations'),

    # ICD APIs
    path('children/<str:inCode>/', views.ListChildrenOfCode.as_view(), name="children-of-code"),
    path('family/<str:inCode>/', views.Family.as_view(), name="family-of-code"),
    path('ancestors/<str:inCode>/', views.ListAncestors.as_view(), name="ancestors-of-code"),
    path('codeAutosuggestions/<str:searchString>/', views.ListCodeAutosuggestions.as_view(), name="code-autosuggestions"),
    path('matchDescription/<str:searchString>/', views.ListMatchingDescriptions.as_view(), name="match-description"),
    path('matchKeyword/<str:searchString>/', views.ListMatchingKeywords.as_view(), name="match-keyword"),
]
