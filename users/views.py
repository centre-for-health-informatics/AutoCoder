from django.http import HttpResponse
from oauth2_provider.views.base import TokenView
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from oauth2_provider.models import get_access_token_model, get_application_model
import json
from oauth2_provider.signals import app_authorized


class CustomTokenView(TokenView):
    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        if status == 200:
            body = json.loads(body)
            access_token = body.get("access_token")
            if access_token is not None:
                token = get_access_token_model().objects.get(
                    token=access_token)
                app_authorized.send(
                    sender=self, request=request,
                    token=token)
                # drop refresh token from response
                body.pop('refresh_token', None)
                # add username and role to response
                body['user'] = {
                    'username': token.user.username,
                    'role': token.user.role,
                    'email': token.user.email
                }
                body = json.dumps(body)
        response = HttpResponse(content=body, status=status)
        for k, v in headers.items():
            response[k] = v
        return response
