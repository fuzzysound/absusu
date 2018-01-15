from controlcenter import Dashboard, widgets
from appserver_rest.models import UserAction, UserAssignment
from experimenter.models import Experiment,Group,Goal
from reward import KPI

class UserassignmentItemList(widgets.ItemList):
    model = UserAssignment
    list_display = ('ip', 'assignment')
'''
class CTRList(widgets.ItemList):
    
    title = 'Click-through Rate'
    model = Goal
    list_display = ('name','track', 'act_subject', 'experiment')
'''
class MyDashboard(Dashboard):
    widgets = [
        UserassignmentItemList,
    ]