import django


class APIConfig(django.apps.AppConfig):
    """
    This is the app configuration of the modelmanager.plugins.browser app.
    """
    name = 'modelmanager.plugins.browser.api'
    verbose_name = 'API'
    label = 'api'
