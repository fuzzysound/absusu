from django.db import models
from django_mysql.models import JSONField



class UserAssignment(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True, unique=True)
    assignment = JSONField(default=dict)


from experimenter.randomizer import get_user_groups

class UserAction(models.Model):
    ip = models.CharField(max_length=100, blank=True, null=True)
    groups = JSONField({})
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('time', )

    def save(self, *args, **kwargs):
        self.groups = get_user_groups(self.ip)
        super(UserAction, self).save(*args, **kwargs)




# TODO: 실험 여러 개일때 어떤 실험의 그룹인지, total impression 기록할 방법