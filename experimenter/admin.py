from django.contrib import admin
from .models import Experiment, Group

class GroupInline(admin.TabularInline):
    model = Group
    extra = 2

class ExperimentAdmin(admin.ModelAdmin):
    fields = ['name', 'start_time', 'end_time']
    inlines = [GroupInline]
    list_display = ('name', 'start_time', 'end_time', 'active_now')
    list_display_links = ('name', )

admin.site.register(Experiment, ExperimentAdmin)