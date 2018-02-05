from django.db import models
import os.path as osp


class Run(models.Model):
    time = models.DateTimeField('Time', auto_now_add=True)
    tags = models.CharField(max_length=1024, blank=True)
    notes = models.TextField('Notes', blank=True)

    def __unicode__(self):
        return u'Run %i' % self.pk


class NameTagged(models.Model):
    class Meta:
        abstract = True
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    tags = models.CharField(max_length=1024, blank=True)


class TaggedValue(NameTagged):
    class Meta:
        abstract = True
    MAX_DIGITS = 16
    DECIMAL_PLACES = 8
    value = models.DecimalField(max_digits=MAX_DIGITS,
                                decimal_places=DECIMAL_PLACES)


class Parameter(TaggedValue):
    pass


class ResultIndicator(TaggedValue):
    pass


class ResultFile(NameTagged):
    file = models.FileField(upload_to="results")
