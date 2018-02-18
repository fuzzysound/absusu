""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/appserver_rest/managers.py
"""
"""
Model managers for custom querysets
"""

from django.db import models
from django.db.models import Q
from django.utils import timezone


# UserActionManager를 위한 custom queryset
class UserActionQuerySet(models.QuerySet):

    # 주어진 실험과 집단에서 해당 action에 해당하는 로그 찾기
    def query_action(self, experiment, group, action, time_after=None, time_before=None):
        """
        :param experiment: Experiment 모델 인스턴스
        :param group: Group 모델 인스턴스
        :param action: 로그의 'action' 값에 해당하는 문자열
        :param time_after(optional): datetime 객체. 이 값이 주어질 경우 이 시간 이후에 쌓인 로그만 검색한다.
        :param time_before(optional): datetime 객체. 이 값이 주어질 경우 이 시간 이전에 쌓인 로그만 검색한다.
        :return: 위 값들로 검색하는 filter
        """
        if time_after is None and time_before is None:
            return self.filter(Q(groups__contains={experiment.name: group.name}) &
                               Q(action__icontains=action)
                               )
        elif time_before is None:
            return self.filter(Q(groups__contains={experiment.name: group.name}) &
                               Q(action__icontains=action) &
                               Q(time__gte=time_after)
                               )
        elif time_after is None:
            return self.filter(Q(groups__contains={experiment.name: group.name}) &
                               Q(action__icontains=action) &
                               Q(time__lte=time_before)
                               )
        else:
            return self.filter(Q(groups__contains={experiment.name: group.name}) &
                               Q(action__icontains=action) &
                               Q(time__gte=time_after) &
                               Q(time__lte=time_before)
                               )


class UserActionManager(models.Manager):

    # Custom queryset 불러오기
    def get_queryset(self):
        return UserActionQuerySet(self.model, using=self._db)

    def query_action(self, experiment, group, action, time_after=None):
        return self.get_queryset().query_action(experiment, group, action, time_after)