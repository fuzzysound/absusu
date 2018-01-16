from controlcenter import Dashboard, widgets
from appserver_rest.models import UserAction, UserAssignment
from experimenter.models import Experiment,Group,Goal
from reward import KPI

class CTRList(widgets.ItemList):
    '''
    This widget displays a list of CTRs
    '''
    title = 'Click-through Rate'
    model = Experiment
    # multiple tables inner join queryset
    queryset = Experiment.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False)\
        .values_list('name','group__name','goal__act_subject')
    list_display = ('name','group__name', 'goal__act_subject', 'get_ctr')
    width = widgets.LARGE

    def get_ctr(self, queryset):
        kpi = KPI()
        return kpi.CTR(*queryset)

class AbsusuDashboard(Dashboard):
    widgets = (
        widgets.Group([CTRList],width = widgets.LARGER, height = 300),
    )

