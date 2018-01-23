### testing server 자체적으로 생성하는 데이터를 정의하는 모델들
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .managers import ExperimentManager, GroupManager

# default 값을 생성하기 위한 함수들

# 현재시각
def get_default_now():
    return timezone.now()

# 종료시간, 현재시각으로부터 일주일 뒤
def get_default_deadline():
    return timezone.now() + timezone.timedelta(days=7)

# 실험을 정의하는 모델
class Experiment(models.Model):

    # default 값으로 지정하기 위한 변수들
    start = get_default_now()
    end = get_default_deadline()

    # 필드
    name = models.CharField(max_length=100, blank=False, null=True, unique=True) # 실험의 이름
    start_time = models.DateTimeField(default=get_default_now) # 실험 시작시간
    end_time = models.DateTimeField(default=get_default_deadline) # 실험 종료시간

    # Custom manager
    objects = ExperimentManager()

    # 만약 migration할 때 table doesn't exist 에러가 발생한다면: http://techstream.org/Bits/Recover-dropped-table-in-Django
    # 만약 test할 때 naive datetime 워닝이 발생한다면: experimenter/migrations 디렉토리에서 __init__.py 빼고 모두 제거

    # 출력 형식
    def __str__(self):
        return self.name # 실험의 이름을 출력

    # 현재 진행되고 있는 실험인가를 관리자 페이지에 나타내기 위한 method
    def active_now(self):
        return self.start_time < timezone.now() < self.end_time # 현재시각이 실험의 시작시간과 종료시간 사이인가
    active_now.short_description = "Active" # 관리자 페이지에 표시될 열 이름
    active_now.boolean = True # 아이콘으로 표시

    # Model validation method
    def clean(self, *args, **kwargs):

        # 시작 시간이 지금보다 이전일 경우
        if self.start_time < timezone.now():
            self.start_time = timezone.now() # 시작 시간을 지금으로 맞춰준다

        # 종료 시간이 시작 시간보다 이전일 경우
        if self.end_time < self.start_time:
            raise ValidationError(_("End time must be later than start time!"), code='end_time_earlier_than_start_time')

        super(Experiment, self).clean(*args, **kwargs)

    # save 이전에 full_clean을 호출해줘야 clean 메소드가 호출된다
    def save(self, *args, **kwargs):
        self.full_clean() # validate
        super(Experiment, self).save(*args, **kwargs)

# 실험의 집단을 정의하는 모델, 실험에 종속적.
class Group(models.Model):

    BOOLEAN_CHOICES = ((True, "Yes"), (False, "No")) # widget에 나타나는 형식을 바꾸기 위한 tuple

    # 필드
    name = models.CharField(max_length=100, blank=False, null=True) # 집단의 이름
    weight = models.IntegerField() # 집단에 피험자가 배정되는 비중
    control = models.BooleanField(default=False, choices=BOOLEAN_CHOICES) # 이 집단이 통제집단인가?
    ramp_up = models.BooleanField(default=False, choices=BOOLEAN_CHOICES) # 이 집단에 ramp up을 사용할 것인가?
    ramp_up_percent = models.FloatField(default=0.5) # ramp up을 사용할 경우 피험자를 몇 %나 배정할 것인지, must be between 0 and 100
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE) # 집단이 속한 실험

    # Custom manager
    objects = GroupManager()

    class Meta:
        unique_together = (('name', 'experiment'), ) # 같은 experiment 안에서 name은 unique하게

    # 출력 형식
    def __str__(self):
        return self.name # 집단의 이름을 출력

    # Validation method
    def clean(self, *args, **kwargs):

        # weight가 양의 정수가 아닐 경우
        if self.weight is None or self.weight < 1:
            raise ValidationError(_("Weight must be a positive integer!"), code='weight_is_non_positive')

        # ramp up percent가 0에서 100 사이의 값이 아닐 경우
        if self.ramp_up_percent > 100 or self.ramp_up_percent < 0:
            raise ValidationError(_("Ramp up percent must be between 0 and 100!"), code='ramp_up_percent_is_not_valid')

    def save(self, *args, **kwargs):
        self.full_clean() # validate
        super(Group, self).save(*args, **kwargs)

# 실험의 목표를 정의하는 모델
class Goal(models.Model):

    SUBJECT_CHOICES = (
        ('clicks', "Clicks"),
        ('pageviews', "Pageviews"),
    ) # widget에 나타나는 형식을 바꾸기 위한 tuple

    #field
    name = models.CharField(max_length=100, blank=False, null=True, unique=True)
    track = models.CharField(max_length=10, choices = SUBJECT_CHOICES, default='clicks')
    act_subject = models.CharField(max_length=100, blank=False, null=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('track','act_subject'),)

    def __str__(self):
        return '%s %s' % (self.experiment, self.name)
