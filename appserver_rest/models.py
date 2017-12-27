from django.db import models

from experimenter.randomizer import get_user_group


class UserAction(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True)
    group = models.CharField(max_length=100, blank=False, null=False, default=get_user_group(ip))
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('time', )

# TODO: 실험 여러 개일때 어떤 실험의 그룹인지, total impression 기록할 방법