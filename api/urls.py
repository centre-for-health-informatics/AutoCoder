from django.urls import path
from api import views

urlpatterns = [
    path('createUser/', views.CreateUser.as_view(), name="create-user"),
    path('validateToken/', views.ValidateToken.as_view(), name="validate-token"),
    path('uploadDoc/', views.UploadDoc.as_view(), name="upload-doc"),
]
