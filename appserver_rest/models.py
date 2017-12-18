from django.db import models

class UserAction(models.Model):
    group = models.CharField(max_length=100, blank=False, null=False, default='A')
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('time', )