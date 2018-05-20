"""browser URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from .api.views import call_project_function, call_run_function


urlpatterns = [
    # function call
    url(r'api/function/(?P<pk>.+)/call/$', call_project_function),
    url(r'browser/run/(?P<rid>\d)/function/(?P<fpk>.+)/call/$',
        call_run_function),
    url(r'', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_title = settings.PROJECT.__module__
admin.site.site_header = admin.site.site_title+': '+settings.PROJECT.projectdir
admin.site.index_title = admin.site.site_title+' administration'
