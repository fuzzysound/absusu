from django.db import models
from django_mysql.models import ListCharField # A field class similar to python list
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .managers import ExperimentManager


class Experiment(models.Model):

    # 시간 default 값으로 쓰일 값들
    now = timezone.now()
    a_week_after_now = now + timezone.timedelta(days=7)

    # 필드
    name = models.CharField(max_length=100, blank=False, null=True, unique=True)
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(default=a_week_after_now)
    ramp_up = models.BooleanField(default=False)

    # Custom manager
    objects = ExperimentManager()

    # 만약 migration할 때 table doesn't exist 에러가 발생한다면: http://techstream.org/Bits/Recover-dropped-table-in-Django
    # 만약 test할 때 naive datetime 워닝이 발생한다면: experimenter/migrations 디렉토리에서 __init__.py 빼고 모두 제거

    # 출력 형식
    def __str__(self):
        return self.name

    def active_now(self):
        _now = timezone.now()
        return self.start_time < _now < self.end_time
    active_now.short_description = "Active"
    active_now.boolean = True
    active_now.empty_value_display = False

    # Model validation method
    def clean(self, *args, **kwargs):

        # 시작 시간이 지금보다 이전일 경우
        if self.start_time < self.now:
            self.start_time = self.now

        # 종료 시간이 시작 시간보다 이전일 경우
        if self.end_time < self.start_time:
            raise ValidationError(_("End time must be later than start time!"), code='end_time_earlier_than_start_time')

        super(Experiment, self).clean(*args, **kwargs)

    # save 이전에 full_clean을 호출해줘야 clean 메소드가 호출된다
    def save(self, *args, **kwargs):
        self.full_clean()
        super(Experiment, self).save(*args, **kwargs)


class Group(models.Model):

    name = models.CharField(max_length=100, blank=False, null=True)
    weight = models.IntegerField()
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name', 'experiment'), ) # 같은 experiment 안에서 name은 unique하게

    def __str__(self):
        return self.name

    def clean(self, *args, **kwargs):

        # weight가 양의 정수가 아닐 경우
        if self.weight < 1:
            raise ValidationError(_("Weight must be a positive integer!"), code='weight_is_non_positive')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Group, self).save(*args, **kwargs)







