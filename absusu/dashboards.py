'''
Show AB test Dashboard
'''
from controlcenter import Dashboard, widgets
from appserver_rest.models import UserAction,UserAssignment
from experimenter.models import Experiment,Group,Goal
from reward import KPI
from django.db.models import Count


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

    def get_ctr(self, queryset):
        kpi = KPI()
        return kpi.CTR(*queryset)

class GroupPieChart(widgets.PieChart):
    '''
    This widget displays allocation of groups each experiment
    '''
    title = 'User Group Allocation'

    class Chartist:
        options = {
            # Displays only integer values on y-axis
            'onlyInteger': True,
            # Visual tuning
            'chartPadding': {
                'top': 10,
                'right': 0,
                'bottom': 0,
                'left': 0,
            },
            # donut chart
            'donut':True,
            'donutWidth': 150,
        }

    def series(self):
        # Y-axis
        return [z for x, y, z in self.values]

    def labels(self):
        # Displays series
        return [x+' '+y+'('+str(z)+')' for x, y, z in self.values]

    def legend(self):
        # Displays labels in legend
        return [x+' '+y for x, y, z in self.values]

    def values(self):
        # Returns a list of tuple type by each element
        # eg)[('exp1', 'control', 2)]
        queryset = UserAction.objects.order_by('ip').values('ip','groups').distinct()\
        .values_list('groups',flat=True).annotate(Count('groups'))
        queryset2 = Experiment.objects.values_list('name','group__name')
        query_list = []

        for i in range(len(queryset2)):
            val_list = list(queryset2[i])
            val_count = eval("queryset.filter(groups__" + queryset2[i][0] + "=\'" + queryset2[i][1] + "\').count()")
            val_list.append(val_count)
            query_list.append(tuple(val_list))
        return query_list

class AbsusuDashboard(Dashboard):
    widgets = (
        widgets.Group([CTRList],width = widgets.LARGE),
        widgets.Group([GroupPieChart], width=widgets.LARGE),
    )
