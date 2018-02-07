"""
This resource directory is copied into the project/resourcedir when the
browser app is installed. It provides the default project specifc django files.
"""

import os.path as osp

from django.conf import settings
from django.apps import AppConfig


class BrowserResourcesConfig(AppConfig):
    """
    This is the django app configuration that sits in the
    project/resourcedir/browser directory.
    """
    name = label = 'browser'
    verbose_name = "Database"
