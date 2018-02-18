""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/experimenter/models.py
"""
"""
testing server 자체적으로 생성하는 데이터를 정의하는 모델들
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.html import format_html
from .managers import ExperimentManager, GroupManager, GoalManager
from .bandit import Bandit
from threading import Timer


# default 값을 생성하기 위한 함수들
# 현재시각
def get_default_now():
    return timezone.now()


# 종료시간, 현재시각으로부터 일주일 뒤
def get_default_deadline():
    return timezone.now() + timezone.timedelta(days=7)


def get_default_ramp_up_deadline():
    return timezone.now() + timezone.timedelta(days=3.5)


# 실험을 정의하는 모델
class Experiment(models.Model):

    # simple은 기본 A/B test, bandit은 multi-armed bandit
    ALGORITHM_CHOICES = (('simple', "Simple"), ('bandit', "Multi-armed Bandit"))

    # 필드
    name = models.CharField(max_length=100, blank=False, null=True, unique=True) # 실험의 이름
    start_time = models.DateTimeField(default=get_default_now) # 실험 시작시간
    end_time = models.DateTimeField(default=get_default_deadline) # 실험 종료시간
    algorithm = models.CharField(max_length=100, choices=ALGORITHM_CHOICES, default='simple') # 사용할 테스트 알고리즘
    assignment_update_interval = models.FloatField(default=24) # must be positive
    auto_termination = models.BooleanField(default=False) # 자동 실험 종료 사용 여부

    # Custom manager
    objects = ExperimentManager()

    # 만약 migration할 때 table doesn't exist 에러가 발생한다면: http://techstream.org/Bits/Recover-dropped-table-in-Django
    # 만약 test할 때 naive datetime 워닝이 발생한다면: experimenter/migrations 디렉토리에서 __init__.py 빼고 모두 제거


    # 출력 형식
    def __str__(self):
        return self.name # 실험의 이름을 출력

    # 현재 진행되고 있는 실험인가를 알기 위한 method
    def active_now(self):
        return self.start_time < timezone.now() < self.end_time # 현재시각이 실험의 시작시간과 종료시간 사이인가

    # 실험이 어떤 상태인지 관리자 페이지에 표시하기 위한 method
    def status(self):
        if timezone.now() < self.start_time: # 실험 시작 이전일 경우
            return format_html('<span style="color:#ceab00">Waiting</span>') # 노란색의 'Waiting' 문구 표시
        elif timezone.now() < self.end_time: # 실험이 진행되 중일 경우
            return format_html('<span style="color:#8ace00; font-weight:bold">Working</span>') # 초록색의 굵은 'Working'
        else: # 실험이 종료되었을 경우
            return format_html('<span style="color:#8d8873">Finished</span>') # 회색의 'Finished'
    status.short_description = 'Status' # 화면에 표시할 이름

    # Bandit algorithm을 활성화하는 method. 관리자 페이지에서 모델 저장할 때 호출됨.
    def activate_bandit(self):
        self.bandit = Bandit(self) # 모델 애트리뷰트로 Bandit 클래스 인스턴스 생성
        if self.start_time <= timezone.now(): # 만약 실험 시작시간이 지금보다 이르면
            self.bandit.update_weights() # 바로 활성화
        else: # 그 외에는
            Timer((self.start_time - timezone.now()).total_seconds(), self.bandit.update_weights).start()
            # 실험 시작시간에 활성화하도록 타이머 생성

    # Model validation method
    def clean(self, *args, **kwargs):

        # 종료 시간이 시작 시간보다 이전일 경우
        if self.end_time < self.start_time:
            raise ValidationError(_("End time must be later than start time!"), code='end_time_earlier_than_start_time')

        # assignment update interval이 양수가 아닐 경우
        if self.assignment_update_interval <= 0:
            raise ValidationError(_("Assignment update interval must be positive!"),
                                  code='assignment_update_interval_not_positive')

        super(Experiment, self).clean(*args, **kwargs)

    # save 이전에 full_clean을 호출해줘야 clean 메소드가 호출된다
    def save(self, *args, **kwargs):
        self.full_clean() # validate
        super(Experiment, self).save(*args, **kwargs)


# 실험의 집단을 정의하는 모델, 실험에 종속적.
class Group(models.Model):

    BOOLEAN_CHOICES = ((True, "Yes"), (False, "No")) # widget에 나타나는 형식을 바꾸기 위한 tuple
    RAMP_UP_CHOICES = (('no', "Don't use"), ('manual', "Manual"), ('automatic', "Automatic")) # 선택 가능한 ramp up의 종류

    # 필드
    name = models.CharField(max_length=100, blank=False, null=True) # 집단의 이름
    weight = models.IntegerField(default=1) # 집단에 피험자가 배정되는 비중
    control = models.BooleanField(default=False, choices=BOOLEAN_CHOICES) # 이 집단이 통제집단인가?
    ramp_up = models.CharField(max_length=100, default='no', choices=RAMP_UP_CHOICES) # 이 집단에 어떤 ramp up을 사용할 것인가?
    ramp_up_percent = models.FloatField(default=0.5)
    # manual ramp up을 사용할 경우 피험자를 몇 %나 배정할 것인지, must be between 0 and 100
    ramp_up_end_time = models.DateTimeField(default=get_default_ramp_up_deadline)
    # automatic ramp up을 사용할 경우 ramp up을 언제 종료할 것인지, 실험 시작시간과 종료시간 사이여야 함
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
        if self.ramp_up == 'manual' and (self.ramp_up_percent > 100 or self.ramp_up_percent < 0):
            raise ValidationError(_("Ramp up percent must be between 0 and 100!"), code='ramp_up_percent_is_not_valid')

    def save(self, *args, **kwargs):
        self.full_clean() # validate
        super(Group, self).save(*args, **kwargs)


# 실험의 목표를 정의하는 모델
class Goal(models.Model):

    SUBJECT_CHOICES = (
        ('clicks', "Click-Through Rate"),
        ('time', "Time on Page"),
    ) # widget에 나타나는 형식을 바꾸기 위한 tuple

    # 필드
    name = models.CharField(max_length=100, blank=False, null=True, unique=True)
    KPI = models.CharField(max_length=10, choices = SUBJECT_CHOICES, default='clicks')
    act_subject = models.CharField(max_length=100, blank=False, null=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    # Custom manager
    objects = GoalManager()

    class Meta:
        unique_together = (('KPI', 'act_subject'),) # KPI와 act_subject를 묶어서 유일하게

    # 출력 형식
    def __str__(self):
        return '%s %s' % (self.experiment, self.name) # 실험과 목표를 출력
