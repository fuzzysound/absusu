""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/experimenter/managers.py
"""
"""
Model managers for custom querysets
"""

from django.db import models
from django.utils import timezone

# Why making explicit querysets? To make chainable filter methods.
# Reference: https://simpleisbetterthancomplex.com/tips/2016/08/16/django-tip-11-custom-manager-with-chainable-querysets.html


class ExperimentQuerySet(models.QuerySet): # ExperimentManager를 위한 custom queryset

    # 현재 active한 실험 찾기
    def active(self):
        now = timezone.now() # 현재시각
        return self.filter(start_time__lte=now, end_time__gte=now) # 현재시각이 실험 시작시간과 종료시간 사이에 있는 실험을 찾는다


class ExperimentManager(models.Manager):

    def get_queryset(self): # Custom queryset 불러오기
        return ExperimentQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    # 지정한 개수만큼 임의의 실험 생성. Test 시에만 사용할 것.
    def create_test_experiments(self, num, algorithm='simple', assignment_update_interval=24, auto_termination=False):
        for i in range(num):
            self.create(name=str(i), algorithm=algorithm, assignment_update_interval=assignment_update_interval,
                        auto_termination=auto_termination)

    # 생성한 실험의 bandigt 활성화. Test 시에만 사용할 것.
    def activate_test_bandits(self):
        from .models import Experiment
        for experiment in Experiment.objects.all():
            experiment.activate_bandit()


class GroupManager(models.Manager):

    # 지정한 개수만큼 각 실험마다 임의의 집단 생성. Test 시에만 사용하며, ExperimentManager의 create_test_experiments와 함께 사용할 것.
    def create_test_groups(self, num, ramp_up='no', ramp_up_percent=0.5,
                           ramp_up_end_time=timezone.now()+timezone.timedelta(days=3.5)):
        from .models import Experiment
        for experiment in Experiment.objects.all(): # 모든 존재하는 실험에 대해
            self.create(name='0', weight=1, control=True, experiment=experiment) # 통제집단 1개 생성
            for i in range(num-1):
                self.create(name=str(i+1), weight=1, control=False, ramp_up=ramp_up,
                            ramp_up_percent=ramp_up_percent, ramp_up_end_time=ramp_up_end_time,
                            experiment=experiment) # num-1개의 실험집단들 생성


class GoalManager(models.Manager):

    # 각 실험마다 임의의 goal 생성. Test 시에만 사용하며, ExperimentManager의 create_test_experiments와 함께 사용할 것.
    def create_test_goals(self, KPI='clicks'):
        from .models import Experiment
        # 모든 실험은 단 한개의 act_subject만 갖는다.
        for experiment in Experiment.objects.all():
            # 실험이름: '0', 실험대상이름: '0'
            self.create(name=experiment.name+'-0', KPI=KPI,
                        act_subject=experiment.name+'-0', experiment_id=experiment.id)