from django.db import models


class Run(models.Model):
    class Meta:
#        abstract = True
        ordering = ['-pk']
    time = models.DateTimeField('Time', auto_now_add=True)
    TYPES = ['testing', 'calibration', 'validation', 'prediction']
    type = models.CharField('Type', max_length=32, default='testing',
                            choices=zip(TYPES, TYPES))
    notes = models.TextField('Notes', blank=True)


class TaggedValue(models.Model):
    class Meta:
        abstract = True

    MAX_DIGITS = 16
    DECIMAL_PLACES = 8

    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    tags = models.CharField(max_length=1024)
    value = models.DecimalField(max_digits=MAX_DIGITS,
                                decimal_places=DECIMAL_PLACES)
    notes = models.TextField('Notes', blank=True)


class Parameter(TaggedValue):
    pass


class Result(TaggedValue):
    pass
