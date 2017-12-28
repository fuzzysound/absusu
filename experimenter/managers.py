# Model managers for custom querysets

from django.db import models
from django.utils import timezone

# Why making explicit querysets? To make chainable filter methods.
# Reference: https://simpleisbetterthancomplex.com/tips/2016/08/16/django-tip-11-custom-manager-with-chainable-querysets.html

class ExperimentQuerySet(models.QuerySet):
    # 현재 active한 실험 찾기
    def active(self):
        now = timezone.now()
        return self.filter(start_time__lte=now, end_time__gte=now)


class ExperimentManager(models.Manager):

    def get_queryset(self):
        return ExperimentQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()