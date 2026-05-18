from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.utils.deprecation import MiddlewareMixin


class TokenAuthMiddleware(MiddlewareMixin):
    """Middleware для авторизации через Token в обычных view"""

    def process_request(self, request):
        if request.path.startswith('/api/'):
            return None

        auth_header = request.headers.get('Authorization')
        token_key = None

        if auth_header and auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
        else:
            token_key = request.COOKIES.get('auth_token')

        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
            except Token.DoesNotExist:
                pass

        return None