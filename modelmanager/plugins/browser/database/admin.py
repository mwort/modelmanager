"""
The global Django admin browser configuration.
"""

from django.contrib import admin
from django.apps import apps

from .admindefault import DefaultModelAdmin


def register_models(applabel):
    app = apps.get_app_config(applabel)
    # register all models defined in browser.models
    for k, m in app.models.items():
        adminclass = m._admin if hasattr(m, '_admin') else DefaultModelAdmin
        admin.site.register(m, adminclass)
    return


register_models('browser')
