from django.db import models

value_help = ("Valid python code, i.e. strings in 'str'."
              "The variable 'project' contains the project.")


class Setting(models.Model):
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=1024, help_text=value_help)


class Function(models.Model):
    name = models.CharField(max_length=64)
    plugin = models.CharField(max_length=64, blank=True)
    doc = models.TextField(verbose_name='Description', blank=True)
    kwargs = models.BooleanField(verbose_name='Accept any keyword',
                                 default=False)


class Argument(models.Model):
    function = models.ForeignKey(Function)
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=64, blank=True, help_text=value_help)
    last_modified = models.DateTimeField(auto_now=True)
