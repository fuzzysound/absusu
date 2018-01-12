### 관리자 페이지를 정의하는 파일
from django.contrib import admin
from .models import Experiment, Group, Goal
from .forms import GroupAdminForm

class GroupInline(admin.StackedInline): # Group 모델을 inline으로 나타내기 위한 클래스
    model = Group
    form = GroupAdminForm
    extra = 0
    min_num = 2 # 최소 2개의 group을 등록하도록 함. TODO: experiment 생성 후 나중에 수정하지 못하도록 해야 함.
    template = 'admin/experimenter/edit_inline/stacked.html'

class GoalInline(admin.TabularInline): # Goal 모델을 inline으로 나타내기 위한 클래스
    model = Goal
    extra = 0
    min_num = 1

class ExperimentAdmin(admin.ModelAdmin): # Experiment 모델을 admin이 수정할 수 있도록 하는 클래스
    fields = ['name', 'start_time', 'end_time'] # 화면에 나타낼 필드들
    inlines = [GroupInline, GoalInline] # inline으로 나타낼 모델들
    list_display = ('name', 'start_time', 'end_time', 'active_now') # 목록 화면에서 나타낼 필드들
    list_display_links = ('name', ) # name 필드를 클릭하면 detail view로 이동하도록

admin.site.register(Experiment, ExperimentAdmin)