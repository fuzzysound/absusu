### Application server와 통신하는 데이터를 정의하는 모델들

from django.db import models
from django_mysql.models import JSONField
from django.urls import reverse
from .managers import UserActionManager

# 유저 행동을 기록하는 모델, application server에 응답함.
class UserAction(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True) # 유저를 식별할 수 있는 IP Address
    groups = JSONField({}) # 각 실험별 유저가 배정된 집단
    time = models.DateTimeField(auto_now_add=True) # 행동이 기록된 시간
    action = models.CharField(max_length=100, blank=True, null=True) # 행동

    # Custom manager
    objects = UserActionManager()

    def get_absolute_url(self): # DetailView로 가기 위한 hyperlink를 제공하는 method
        return reverse('useraction-detail', args=[str(self.id)])
        # 'useraction-detail'은 DRF router에서 default로 제공하는 DetailView의 url name임.

    class Meta:
        ordering = ('-time', ) # 최신순으로 정렬
        indexes = [models.Index(fields=['time'], name='time_idx')]


# 유저가 어느 hash partition에 할당되었는지 기록하는 모델
class UserAssignment(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True, unique=True) # IP Address
    hash_indexes = JSONField(default=dict) # 각 실험별 유저가 배정된 hash index

    def get_absolute_url(self): # UserAction의 get_absolute_url()과 같은 기능
        return reverse('userassignment-detail', args=[str(self.id)])

