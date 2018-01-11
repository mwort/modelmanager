from django.contrib.auth.models import User, Group
from django.contrib import admin
from django.apps import apps


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
            defaultuser = dict(username='modelmanager', password='1', email='')
            request.user = User.objects.create_superuser(**defaultuser)

        response = self.get_response(request)

        return response


def register_models(applabel):
    app = apps.get_app_config(applabel)
    # register all models defined in browser.models
    for k, m in app.models.items():
        admin.site.register(m)
    return


admin.site.unregister(User)
admin.site.unregister(Group)
register_models('modelmanager')
register_models('browser')
