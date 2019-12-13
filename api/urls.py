from django.urls import path
from api import views

urlpatterns = [
    path('validateToken/', views.ValidateToken.as_view(), name="validate-token"),
]
