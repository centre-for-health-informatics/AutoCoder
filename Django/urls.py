from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),  # Added for OAuth2
    # path('accounts/login/', auth_views.LoginView.as_view(), name="login"),
    #path('accounts/', include('accounts.urls')),
    #path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('api.urls')),
    # path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]
urlpatterns += staticfiles_urlpatterns()
