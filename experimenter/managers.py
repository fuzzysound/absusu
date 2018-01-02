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

    # 지정한 개수만큼 임의의 실험 생성. Test 시에만 사용할 것.
    def create_test_experiments(self, num):
        for i in range(num):
            self.create(name=str(i))


class GroupManager(models.Manager):

    # 지정한 개수만큼 각 실험마다 임의의 집단 생성. Test 시에만 사용하며, ExperimentManager의 create_test_experiments와 함께 사용할 것.
    def create_test_groups(self, num):
        from .models import Experiment
        for experiment in Experiment.objects.all():
            for i in range(num):
                self.create(name=str(i), weight=1, experiment=experiment)