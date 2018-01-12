### Application server와 통신하는 데이터를 정의하는 모델들

from django.db import models
from django_mysql.models import JSONField

# 유저 행동을 기록하는 모델, application server에 응답함.
class UserAction(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True) # 유저를 식별할 수 있는 IP Address
    groups = JSONField({}) # 각 실험별 유저가 배정된 집단
    time = models.DateTimeField(auto_now_add=True) # 행동이 기록된 시간
    action = models.CharField(max_length=100, blank=True, null=True) # 행동

    class Meta:
        ordering = ('time', ) # 시간 순으로 정렬


# 유저가 어느 hash partition에 할당되었는지 기록하는 모델
class UserAssignment(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True, unique=True) # IP Address
    hash_indexes = JSONField(default=dict) # 각 실험별 유저가 배정된 hash index

