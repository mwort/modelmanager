from django.db import models

TYPES = {str: ('str', 'String'),
         int: ('int', 'Integer'),
         float: ('float', 'Float'),
         bool: ('bool', 'True/False'),
         object: ('setting', 'Project setting')}


class Setting(models.Model):
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=1024)


class Function(models.Model):
    name = models.CharField(max_length=64)
    plugin = models.CharField(max_length=64, blank=True)
    doc = models.TextField(verbose_name='Description', blank=True)
    kwargs = models.BooleanField(default=False)


class Argument(models.Model):
    function = models.ForeignKey(Function)
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=16, default='str',
                            choices=TYPES.values())
    value = models.CharField(max_length=64, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)
