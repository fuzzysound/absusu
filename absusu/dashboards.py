'''
Show AB test Dashboard
'''
from controlcenter import Dashboard, widgets
from controlcenter.widgets.core import WidgetMeta
from appserver_rest.models import UserAction
from experimenter.models import Experiment
from reward import KPI
from django.utils import timezone
import datetime

# Active Experiments list
# eg) EXPERIMENTS = ['exp1', 'exp2', 'exp3', ]
EXPERIMENTS = [experiment.name for experiment in Experiment.objects.all()]

# to show a list of CTR for each experiment
class CTRList(widgets.ItemList):
    '''
    This widget displays a list of CTRs
    '''
    title = 'Click-through Rate'
    model = Experiment
    # multiple tables inner join queryset
    queryset = model.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False)\
        .values_list('name','group__name','goal__act_subject')
    list_display = ('name','group__name', 'goal__act_subject', 'get_ctr')

    def get_ctr(self, queryset):
        kpi = KPI()
        today = timezone.now().date()
        return kpi.CTR(*queryset, today)

# to show a pie chart how users are allocated for each group in experiment
class GroupPieChart(widgets.PieChart):
    '''
    This widget displays allocation of groups each experiment
    '''
    title = 'User Group Allocation'
    queryset = UserAction.objects.order_by('ip').values('ip', 'groups').distinct() \
        .values_list('groups', flat=True)
    queryset2 = Experiment.objects.values_list('name', 'group__name')
    query_list = []
    # eg)[('exp1', 'control', 2)]

    for i in range(len(queryset2)):
        val_list = list(queryset2[i])
        val_count = eval("len(queryset.filter(groups__" + queryset2[i][0] + "=\'" + queryset2[i][1] + "\'))")
        val_list.append(val_count)
        query_list.append(tuple(val_list))

    class Chartist:
        options = {
            # Displays only integer values on y-axis
            'onlyInteger': True,

            # Visual tuning
            'chartPadding': 50,
            'labelDirection':'explode',
            'labelOffset':50,

            # donut chart
            'donut':True,
            'donutWidth': 50,
            'donutSolid': True,
        }

    def series(self):
        # Y-axis
        return [z for x, y, z in self.query_list]

    def labels(self):
        # Displays series
        return [x+' '+y+' ('+str(z)+')' for x, y, z in self.query_list]

    def legend(self):
        # Displays labels in legend
        return [x+' '+y for x, y, z in self.query_list]


class TimeLineChart(widgets.LineChart):
    # Display flow of CTRs during experiment
    title = 'Click-through Rate Time Series'
    leg_queryset = Experiment.objects.filter(group__name__isnull=False).values_list('name', 'group__name')
    val_queryset = Experiment.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False) \
                .values_list('name', 'group__name', 'goal__act_subject')

    class Chartist:
        # visual tuning
        options = {
            'axisX': {
                'labelOffset': {
                    'x': -50,
                    'y': 10
                },

            },
            'lineSmooth':False,
            'chartPadding': {
                'top': 50,
                'left': 50,
                'right': 50,
                'bottom': 20,
            }
        }

    # to specify experiment period
    @classmethod
    def elapsed_time(cls, exp_name):
        started = [datetime['start_time'] for datetime in Experiment.objects.filter(name=exp_name).values('start_time')][0]
        today = timezone.now()
        elapsed_time = (today - started).days + 2
        return elapsed_time

    # to specify experiment name, group name
    def legend(self):
        return [exp_name + ' ' + group_name for exp_name, group_name in self.leg_queryset]
    '''
    legend queryset format
    <ExperimentQuerySet [('exp1', 'A'), ('exp1', 'B'), ('exp2', 'control'), ('exp2', 'test')]>
    '''

    # to represent values on x-axis such as date. ex) 2018-01-18
    def labels(self):
        today = timezone.now().date()
        labels = [(today - datetime.timedelta(days=x)).strftime('%Y-%m-%d') for x in range(self.elapsed_time)]
        return labels
    '''
    labels format
    ['2018-01-18',
     '2018-01-17',
     '2018-01-16',
     '2018-01-15',
     '2018-01-14',
     '2018-01-13',
     '2018-01-12']
    '''

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
    '''
    series format
    [[0.6, 0.6, 0.5, 0, 0, 0, 0],
     [0.9, 0.778, 0.857, 0, 0, 0, 0],
     [0.538, 0.571, 0.5, 0, 0, 0, 0],
     [0.444, 0.429, 0.333, 0, 0, 0, 0]]
    '''

    # to calculate values such as CTR. ex) 0.725
    def values(self):
        kpi = KPI()
        values = dict()
        for label in self.labels:
            alist = list()
            for exp_name, group_name, act_subject in self.val_queryset:
                alist.append(kpi.CTR(exp_name, group_name, act_subject, label))
            values[label] = alist
        return values
    '''
    values format
    {'2018-01-12': [0, 0, 0, 0],
     '2018-01-13': [0, 0, 0, 0],
     '2018-01-14': [0, 0, 0, 0],
     '2018-01-15': [0, 0, 0, 0],
     '2018-01-16': [0.333, 0.5, 0.857, 0.5],
     '2018-01-17': [0.429, 0.571, 0.778, 0.6],
     '2018-01-18': [0.444, 0.538, 0.9, 0.6]}
        }
    '''

# Metaclass arguments are: class name, base, properties.
CTRLists = [WidgetMeta('{}CTRLists'.format(name),
                       (CTRList,),
                       {'queryset': (CTRList.queryset.filter(name=name)),
                        'title': name + ' CTR',
                        'changelist_url': (
                            Experiment, {'Experiment__name__exact': name})}) for name in EXPERIMENTS]

GroupPieCharts = [WidgetMeta('{}GroupPieCharts'.format(name),
                       (GroupPieChart,),
                       {'query_list': ([t for t in GroupPieChart.query_list if t[0].startswith(name)]),
                        'title': name + ' User Group',
                        'changelist_url': (
                            Experiment, {'Experiment__name__exact': name})}) for name in EXPERIMENTS]

TimeLineCharts = [WidgetMeta('{}TimeLineCharts'.format(name),
                       (TimeLineChart,),
                       {'leg_queryset': (TimeLineChart.leg_queryset.filter(name=name)),
                        'val_queryset': (TimeLineChart.val_queryset.filter(name=name)),
                        'elapsed_time': (TimeLineChart.elapsed_time(name)),
                        'title': name + ' CTR TimeSeries',
                        'changelist_url': (
                            Experiment, {'Experiment__name__exact': name})}) for name in EXPERIMENTS]

# Specifying which widgets to use
class AbsusuDashboard(Dashboard):
    widgets = (
        widgets.Group(CTRLists, width=widgets.LARGE),
        widgets.Group(GroupPieCharts, width=widgets.LARGE),
        widgets.Group(TimeLineCharts, width=widgets.FULL),
)