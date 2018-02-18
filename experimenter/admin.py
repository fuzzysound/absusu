""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/experimenter/admin.py
"""
"""
관리자 페이지를 정의하는 파일
"""
from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as AdminGroup
from .models import Experiment, Group, Goal
from .forms import *
from django.utils.translation import gettext_lazy as _


# Status 필터를 적용하기 위한 클래스
class StatusListFilter(admin.SimpleListFilter):
    title = _('Status') # 필터 이름
    parameter_name = 'status' # 파라미터 이름

    # 선택지 생성: All, Waiting, Working, Finished
    def lookups(self, request, model_admin):
        return(
            (None, _('All')),
            ('waiting', _('Waiting')),
            ('working', _('Working')),
            ('fiished', _('Finished'))
        )

    # 선택지 제한 (default로 존재하는 '모두'를 없앰)
    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': changelist.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    # 쿼리 설정
    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.all()
        elif self.value() == 'waiting':
            return queryset.filter(start_time__gte=timezone.now())
        elif self.value() == 'working':
            return queryset.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now())
        else:
            return queryset.filter(end_time__lte=timezone.now())


class GroupInline(admin.StackedInline): # Group 모델을 inline으로 나타내기 위한 클래스
    model = Group
    form = GroupAdminForm
    fields = ('name', 'control', 'weight', 'ramp_up', 'ramp_up_percent', 'ramp_up_end_time') # 필드 순서 설정
    extra = 0 # Default 값이 2인 extra를 0으로 설정해야 min_num 값이 제대로 설정된다
    min_num = 2 # 최소 2개의 group을 등록하도록 함.
    template = 'admin/experimenter/edit_inline/stacked.html' # JavaScript 동작을 위한 static file overriding

    # 실험 수정할 때 수정을 제한할 필드 설정
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['name']
        else:
            return []


class GoalInline(admin.TabularInline): # Goal 모델을 inline으로 나타내기 위한 클래스
    model = Goal
    extra = 0
    can_delete = 0 # goal을 삭제하지 못하도록 함
    min_num = 1 # 최소 1개의 goal을 등록하도록 함.

    # 실험 수정할 때 수정을 제한할 필드 설정
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['name', 'KPI', 'act_subject']
        else:
            return []


class ExperimentAdmin(admin.ModelAdmin): # Experiment 모델을 admin이 수정할 수 있도록 하는 클래스
    form = ExperimentAdminForm
    fields = ['name', 'start_time', 'end_time', 'algorithm', 'assignment_update_interval',
              'auto_termination',] # 화면에 나타낼 필드들
    inlines = [GroupInline, GoalInline] # inline으로 나타낼 모델들
    list_display = ('name', 'start_time', 'end_time', 'status') # 목록 화면에서 나타낼 필드들
    list_display_links = ('name', ) # name 필드를 클릭하면 detail view로 이동하도록
    list_filter = (StatusListFilter,) # Status를 필터로 쓸 수 있도록 등록

    # 실험 수정할 때 수정을 제한할 필드 설정
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['name', 'start_time', 'end_time', 'algorithm']
        else:
            return []

    # 실험을 새로 생성할 때 호출되는 method를 override
    def response_add(self, request, obj, post_url_continue=None):
        if obj.start_time <= timezone.now(): # 시작 시간이 지금보다 이전일 경우
            obj.start_time = timezone.now() # 시작 시간을 지금으로 맞춰준다
        if obj.algorithm == 'bandit': # 사용하는 알고리즘이 bandit이면
            obj.activate_bandit() # bandit 활성화
        return super().response_add(request, obj, post_url_continue)


# 커스텀 관리자 페이지
class AbsusuAdminSite(admin.AdminSite):
    site_header = 'absusu' # 관리자 페이지 상단에 표시할 이름
    site_title = 'absusu' # 탭에 표시할 이름


absusu_admin = AbsusuAdminSite() # 관리자 페이지 인스턴스 생성
absusu_admin.register(Experiment, ExperimentAdmin) # Experiment 모델을 관리자 페이지에 등록
absusu_admin.register(User) # 관리자를 관리하는 User 모델을 관리자 페이지에 등록
absusu_admin.register(AdminGroup) # 관리자의 그룹을 관리하는 Group 모델을 관리자 페이지에 등록