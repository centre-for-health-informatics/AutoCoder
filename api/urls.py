from django.urls import path
from api import views

urlpatterns = [
    path('createUser/', views.CreateUser.as_view(), name="create-user"),
    path('validateToken/', views.ValidateToken.as_view(), name="validate-token"),
    path('uploadDoc/', views.UploadDoc.as_view(), name="upload-doc"),
    path('uploadAnnot/', views.UploadAnnotation.as_view(), name="upload-annot"),
    path('getAllMyAnnots/',
         views.GetAllAnnotationsByCurrentUserWithPagination.as_view(), name="get-all-my-annot"),
    path('getAnnotationsByFilenameUser/<str:filename>/',
         views.GetAnnotationsByFilenameUser.as_view(), name="get-annotations-filename-user"),
    path('getLastAnnot/<str:filename>/', views.GetLatestAnnotation.as_view(), name="get-last-annot"),
    path('exportAnnotations/<str:sessionId>/', views.ExportAnnotations.as_view(), name='export-annotations'),
    path('downloadAnnotations/<str:id>/', views.DownloadAnnotationsById.as_view(), name='download-annotations')
]
