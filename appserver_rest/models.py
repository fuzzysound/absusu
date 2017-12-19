from django.db import models
from experimenter.randomizer import *

class UserAction(models.Model):
    user_id = models.CharField(max_length=100, blank=True, null=True)
    group = models.CharField(max_length=100, blank=False, null=False, default=get_user_group(user_id))
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('time', )