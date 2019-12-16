from django.urls import path
from api import views

urlpatterns = [
    path('createUser/', views.CreateUser.as_view(), name="create-user"),
    path('validateToken/', views.ValidateToken.as_view(), name="validate-token"),
    path('uploadDoc/', views.UploadDoc.as_view(), name="upload-doc"),
    path('uploadAnnot/', views.UploadAnnotation.as_view(), name="upload-annot"),
    path('getAnnot/<str:filename>/', views.GetAnnotation.as_view(), name="get-annot"),
    path('getLastAnnot/<str:filename>/', views.GetLatestAnnotation.as_view(), name="get-last-annot")
]
