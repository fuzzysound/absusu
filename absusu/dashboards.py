from controlcenter import Dashboard, widgets
from appserver_rest.models import UserAction, UserAssignment
from experimenter.models import Experiment,Group,Goal
from reward import KPI

class UserassignmentItemList(widgets.ItemList):
    model = UserAssignment
    list_display = ('ip', 'assignment')

class CTRList(widgets.ItemList):
    title = 'Click-through Rate'
    model = Experiment
    queryset = Experiment.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False)\
        .values('name','group__name','goal__act_subject')
    list_display = ('name','group__name', 'goal__act_subject', 'get_ctr')


    def get_ctr(self, queryset):
        kpi = KPI()
        return kpi.CTR()

class MyDashboard(Dashboard):
    widgets = [
        UserassignmentItemList,
        CTRList,
    ]