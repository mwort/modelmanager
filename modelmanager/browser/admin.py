from django.contrib.auth.models import User


class NoAuthentication(object):
    '''Middleware to fake user authentication with a fake user.
    settings.py adjustment:
    - replace 'django.contrib.auth.middleware.AuthenticationMiddleware'
      with this class in MIDDLEWARE
    '''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.user = User.objects.filter()[0]
        except IndexError:
            defaultuser = dict(username='mmuser', password='123', email='')
            request.user = User.objects.create_superuser(**defaultuser)

        response = self.get_response(request)

        return response
