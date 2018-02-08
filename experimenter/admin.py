### 관리자 페이지를 정의하는 파일
from django.contrib import admin
from django.utils import timezone
from .models import Experiment, Group, Goal
from .forms import ExperimentAdminForm, GroupAdminForm

class GroupInline(admin.StackedInline): # Group 모델을 inline으로 나타내기 위한 클래스
    model = Group
    form = GroupAdminForm
    extra = 0 # Default 값이 2인 extra를 0으로 설정해야 min_num 값이 제대로 설정된다
    min_num = 2 # 최소 2개의 group을 등록하도록 함.
    template = 'admin/experimenter/edit_inline/stacked.html' # JavaScript 동작을 위한 static file overriding

class GoalInline(admin.TabularInline): # Goal 모델을 inline으로 나타내기 위한 클래스
    model = Goal
    extra = 0
    min_num = 1 # 최소 1개의 goal을 등록하도록 함.

class ExperimentAdmin(admin.ModelAdmin): # Experiment 모델을 admin이 수정할 수 있도록 하는 클래스
    form = ExperimentAdminForm
    fields = ['name', 'start_time', 'end_time', 'algorithm', 'assignment_update_interval'] # 화면에 나타낼 필드들
    inlines = [GroupInline, GoalInline] # inline으로 나타낼 모델들
    list_display = ('name', 'start_time', 'end_time', 'active_now') # 목록 화면에서 나타낼 필드들
    list_display_links = ('name', ) # name 필드를 클릭하면 detail view로 이동하도록

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['start_time', 'end_time', 'algorithm']
        else:
            return []

    # 실험을 새로 생성할 때 호출되는 method를 override
    def response_add(self, request, obj, post_url_continue=None):
        if obj.start_time <= timezone.now(): # 시작 시간이 지금보다 이전일 경우
            obj.start_time = timezone.now() # 시작 시간을 지금으로 맞춰준다
        if obj.algorithm == 'bandit': # 사용하는 알고리즘이 bandit이면
            obj.activate_bandit() # bandit 활성화
        return super().response_add(request, obj, post_url_continue)

admin.site.register(Experiment, ExperimentAdmin) # Experiment 모델을 관리자 페이지에 등록