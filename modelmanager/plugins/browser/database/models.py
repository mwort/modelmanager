"""
This is a collection of meta models to be subclassed in the projects
browser/models.py file.
"""

from django.db import models
from django.core.files import File as djFile


class Run(models.Model):
    class Meta:
        abstract = True
    time = models.DateTimeField('Time', auto_now_add=True)
    tags = models.CharField(max_length=1024, blank=True)
    notes = models.TextField('Notes', blank=True)

    def __unicode__(self):
        return u'Run %i' % self.pk


class RunTagged(models.Model):
    class Meta:
        abstract = True
    run = models.ForeignKey('browser.Run', on_delete=models.CASCADE)
    tags = models.CharField(max_length=1024, blank=True)


class TaggedValue(RunTagged):
    class Meta:
        abstract = True
    MAX_DIGITS = 16
    DECIMAL_PLACES = 8
    name = models.CharField(max_length=128)
    value = models.DecimalField(max_digits=MAX_DIGITS,
                                decimal_places=DECIMAL_PLACES)


class File(RunTagged):
    class Meta:
        abstract = True

    file = models.FileField(upload_to="results")

    def __init__(self, *args, **kwargs):
        # handle different file objects on construction
        if 'file' in kwargs:
            f = kwargs.pop('file')
            if type(f) == str:
                f = file(f, 'rb+')
            if isinstance(f, file):
                f = djFile(f)
            if isinstance(f, djFile):
                kwargs['file'] = f
            else:
                raise TypeError('file must be a path string, a file or a '
                                'django.core.files.File instance.')
        super(File, self).__init__(*args, **kwargs)

    def delete(self):
        self.file.delete()
        super(File, self).delete()