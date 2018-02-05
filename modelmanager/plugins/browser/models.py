from django.db import models


class Run(models.Model):
    time = models.DateTimeField('Time', auto_now_add=True)
    tags = models.CharField(max_length=1024, blank=True)
    notes = models.TextField('Notes', blank=True)

    def __unicode__(self):
        return u'Run %i' % self.pk


class TaggedValue(models.Model):
    class Meta:
        abstract = True

    MAX_DIGITS = 16
    DECIMAL_PLACES = 8

    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    value = models.DecimalField(max_digits=MAX_DIGITS,
                                decimal_places=DECIMAL_PLACES)
    tags = models.CharField(max_length=1024, blank=True)


class Parameter(TaggedValue):
    pass


class Result(TaggedValue):
    pass
