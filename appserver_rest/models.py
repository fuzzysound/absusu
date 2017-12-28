from django.db import models
from django_mysql.models import JSONField

# 유저가 어느 집단에 할당되었는지(Ramp up 사용할 경우엔 어느 hash partition에 할당되었는지) 기록하는 모델
class UserAssignment(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True, unique=True)
    assignment = JSONField(default=dict)


from experimenter.randomizer import get_user_groups

# 유저 행동을 기록하는 모델, application server에 응답함.
class UserAction(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True)
    groups = JSONField({})
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('time', )

    def save(self, *args, **kwargs):
        self.groups = get_user_groups(self.ip) # randomization
        super(UserAction, self).save(*args, **kwargs)




# TODO: total impression 기록할 방법