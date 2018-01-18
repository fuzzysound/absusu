'''
Show AB test Dashboard
'''
from controlcenter import Dashboard, widgets
from appserver_rest.models import UserAction,UserAssignment
from experimenter.models import Experiment,Group,Goal
from reward import KPI
from django.utils import timezone
import datetime
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
        today = timezone.now().date()
        return kpi.CTR(*queryset, today)


class MyLineChart(widgets.LineChart):
    # Displays orders dynamic for last 7 days
    title = 'Click-through Rate Time Series'
    limit_to = 7

    class Chartist:
        # visual tuning
        options = {
            'axisX': {
                'labelOffset': {
                    'x': -50,
                    'y': 10
                },

            },
            'chartPadding': {
                'top': 50,
                'left': 50,
                'right': 50,
                'bottom': 20,
            }
        }

    # to specify experiment name, group name
    def legend(self):
        queryset = Experiment.objects.filter(group__name__isnull=False).values_list('name', 'group__name')
        return queryset
    '''
    legend queryset format
    <ExperimentQuerySet [('exp1', 'A'), ('exp1', 'B'), ('exp2', 'control'), ('exp2', 'test')]>'''

    # to represent values on x-axis such as date. ex) 2018-01-18
    def labels(self):
        today = timezone.now().date()
        labels = [(today - datetime.timedelta(days=x)).strftime('%Y-%m-%d') for x in range(self.limit_to)]
        return labels
    '''
    labels format
    ['2018-01-18',
     '2018-01-17',
     '2018-01-16',
     '2018-01-15',
     '2018-01-14',
     '2018-01-13',
     '2018-01-12']'''

    # to represent values on y-axis which is calculated by values()
    def series(self):
        series = []
        for legend_idx in range(len(self.legend)-1, -1, -1):
            alist = []
            for label in self.labels:
                result = self.values.get(label, {})[legend_idx]
                alist.append(result)
            series.append(alist)
        return series
    """series format
    [[0.6, 0.6, 0.5, 0, 0, 0, 0],
     [0.9, 0.778, 0.857, 0, 0, 0, 0],
     [0.538, 0.571, 0.5, 0, 0, 0, 0],
     [0.444, 0.429, 0.333, 0, 0, 0, 0]]"""

    # to calculate values such as CTR. ex) 0.725
    def values(self):
        queryset = Experiment.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False) \
            .values_list('name', 'group__name', 'goal__act_subject')

        kpi = KPI()
        values = dict()
        for label in self.labels:
            alist = list()
            for exp_name, group_name, act_subject in queryset:
                alist.append(kpi.CTR(exp_name, group_name, act_subject, label))
            values[label] = alist
        return values
    """
    values format
    {'2018-01-12': [0, 0, 0, 0],
     '2018-01-13': [0, 0, 0, 0],
     '2018-01-14': [0, 0, 0, 0],
     '2018-01-15': [0, 0, 0, 0],
     '2018-01-16': [0.333, 0.5, 0.857, 0.5],
     '2018-01-17': [0.429, 0.571, 0.778, 0.6],
     '2018-01-18': [0.444, 0.538, 0.9, 0.6]}
        }
        """


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
        widgets.Group([CTRList], width=widgets.LARGE),
        widgets.Group([GroupPieChart], width=widgets.LARGE),
        widgets.Group([MyLineChart], width=widgets.LARGER, height=500),
    )
