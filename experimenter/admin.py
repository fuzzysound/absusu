from django.contrib import admin
from .models import Experiment, Group

class GroupInline(admin.TabularInline):
    model = Group
    extra = 0
    min_num = 2 # 최소 2개의 group을 등록하도록 함. TODO: experiment 생성 후 나중에 수정하지 못하도록 해야 함.

class ExperimentAdmin(admin.ModelAdmin):
    fields = ['name', 'start_time', 'end_time']
    inlines = [GroupInline]
    list_display = ('name', 'start_time', 'end_time', 'active_now')
    list_display_links = ('name', )

admin.site.register(Experiment, ExperimentAdmin)
