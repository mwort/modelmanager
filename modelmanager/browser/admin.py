from django.contrib.auth.models import User, Group
from django.contrib import admin


def setup(modelsmodule):
    unregister_defaults()
    register_all_models(modelsmodule)
    return


def register_all_models(modelsmodule):
    # register all models defined in browser.models
    admin.site.register([cls for name, cls in modelsmodule.__dict__.items()
                         if isinstance(cls, type)])
    return


def unregister_defaults():
    admin.site.unregister(User)
    admin.site.unregister(Group)
    return


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
