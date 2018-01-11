"""
Your project-specific database tables (django calls them 'models').
Here is an example:

```
from modelmanager.plugins.browser.models import Run

class Output_XYZ(models.Model):
    name = models.CharField(max_length=100)
    time = models.DateTimeField('Time', auto_now_add=True)
    type = models.FloatField('xyzmetric')
    run = models.OneToOneField(Run, on_delete=models.CASCADE)
```

Refer to https://docs.djangoproject.com/en/dev/ref/models/fields/ for fields
and documentation.
"""

from django.db import models
