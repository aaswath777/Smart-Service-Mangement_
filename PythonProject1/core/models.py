from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base class: gives every model that inherits from it
    created_at and updated_at columns. 'abstract = True' means Django
    does NOT create a table for this class itself.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True