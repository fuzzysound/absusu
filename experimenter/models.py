from django.db import models
from django_mysql.models import ListCharField # A field class similar to python list
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from math import isclose

class Experiment(models.Model):

    # 시간 default 값으로 쓰일 값들
    now = timezone.now()
    a_week_after_now = now + timezone.timedelta(days=7)

    # 필드
    name = models.CharField(max_length=100, blank=True, null=True)
    groups = ListCharField(base_field=models.CharField(max_length=100), max_length=10000)
    ratio = ListCharField(base_field=models.CharField(max_length=100), max_length=200)
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(default=a_week_after_now)

    # 만약 migration할 때 table doesn't exist 에러가 발생한다면: http://techstream.org/Bits/Recover-dropped-table-in-Django
    # 만약 test할 때 naive datetime 워닝이 발생한다면: experimenter/migrations 디렉토리에서 __init__.py 빼고 모두 제거

    # 출력 형식
    def __str__(self):
        return self.name

    # Model validation method
    def clean(self, *args, **kwargs):

        # name 필드가 빈칸일 경우
        if self.name == "":
            raise ValidationError(_("Name cannot be blank!"), code='name_is_blank')

        # 집단 개수가 2개 미만일 경우
        if len(self.groups) < 2:
            raise ValidationError(_("The number of groups must be at least 2!"),
                                  code='num_of_groups_less_than_two')

        # 집단 개수와 비율 개수가 일치하지 않을 경우
        if len(self.groups) != len(self.ratio):
            raise ValidationError(_("Groups and ratio must have same length!"),
                                  code='groups_ratio_length_does_not_match')

        # 비율의 합이 1이 아닐 경우 (혹은 1에 근사하지 않을 경우)
        if not isclose(sum(map(float, self.ratio)), 1):
            raise ValidationError(_("Sum of ratio must be 1!"), code='sum_of_ratio_is_not_valid')

        # 시작 시간이 지금보다 이전일 경우
        if self.start_time < self.now:
            raise ValidationError(_("Start time must be later than now!"), code='start_time_earlier_than_now')

        # 종료 시간이 시작 시간보다 이전일 경우
        if self.end_time < self.start_time:
            raise ValidationError(_("End time must be later than start time!"), code='end_time_earlier_than_start_time')

        super(Experiment, self).clean(*args, **kwargs)

    # save 이전에 full_clean을 호출해줘야 clean 메소드가 호출된다
    def save(self, *args, **kwargs):
        self.full_clean()
        super(Experiment, self).save(*args, **kwargs)






