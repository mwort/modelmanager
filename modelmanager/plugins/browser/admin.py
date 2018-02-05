"""
The global Django admin browser configuration.
"""
import csv

from django.contrib.auth.models import User, Group
from django.contrib import admin
from django.apps import apps
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.safestring import mark_safe

if True:  # PY 27
    import StringIO as io
else:
    import io


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


def export_to_csv(modeladmin, request, queryset):
    """
    Action to export a queryset to csv file.

    Only PY2.7 supported, converting everything to str.
    """
    buf = io.StringIO()
    headers = [str(f.name) for f in queryset.model._meta.fields]
    writer = csv.writer(buf)
    writer.writerow(headers)

    for obj in queryset:
        row = []
        for field in headers:
            val = getattr(obj, field)
            row.append(str(val))
        writer.writerow(row)
    buf.seek(0)
    response = HttpResponse(buf, content_type='text/csv')
    content = ('attachment; filename=%s.csv'
               % queryset.model._meta.verbose_name_raw)
    response['Content-Disposition'] = content
    return response


def make_default_model_admin(model):
    meta = model._meta
    fields = meta.fields
    field_names = [f.name for f in fields]

    # make links out of ForeignKey s
    for f in fields:
        if f.get_internal_type() == 'ForeignKey':
            field_names[field_names.index(f.name)] = related_model_link(f)
    # add inlines for related models
    related_inlines = [make_default_inline(m.related_model)
                       for m in meta.related_objects]

    # also show readonly_fields including the id
    rofields = [f.name for f in fields if not f.editable]

    # an admin showing all columns in reverse ID order
    class DefaultModelAdmin(admin.ModelAdmin):
        ordering = ['-id']
        list_display = field_names
        readonly_fields = rofields
        inlines = related_inlines
        list_display_links = field_names
        search_fields = field_names
        list_filter = simple_filter_fields(fields)
        actions = [export_to_csv]

    return DefaultModelAdmin


def simple_filter_fields(fields):
    filterable = ("BooleanField CharField DateField DateTimeField "
                  "IntegerField ForeignKey ManyToManyField".split())
    return [f.name for f in fields if f.get_internal_type() in filterable]


def make_default_inline(ilmodel):
    class DefaultInlineAdmin(admin.TabularInline):
        model = ilmodel
        classes = ['collapse']
        extra = 0
    return DefaultInlineAdmin


def related_model_link(field):
    def link_fk(obj):
        relmodel = getattr(obj, field.name)
        href = '<a href="{}">{}</a>'
        urlname = ("admin:%s_%s_change" % (relmodel._meta.app_label,
                   relmodel._meta.verbose_name_raw))
        url = reverse(urlname, args=(relmodel.pk,))
        return mark_safe(href.format(url, relmodel.pk))
    link_fk.short_description = field.name
    return link_fk


def register_models(applabel):
    app = apps.get_app_config(applabel)
    # register all models defined in browser.models
    for k, m in app.models.items():
        admin.site.register(m, make_default_model_admin(m))
    return


admin.site.unregister(User)
admin.site.unregister(Group)
register_models('modelmanager')
register_models('browser')
