""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/absusu/views.py
"""
from appserver_rest.models import UserAction
from experimenter.models import Experiment
from reward import KPI
from collections import Counter
from django.utils import timezone
import json
from django.http import HttpResponse


# GroupPieChart view function
def pie_data(request):
    """
    takes a HTTP GET request and returns a JSON response of PieChart data.
    :param request: HTTP
    :return: HttpResponse as json type
    """

    if request.method == 'GET':
        # get request
        exp = request.GET.get('exp')
        # queryset
        val_queryset = UserAction.objects.order_by('ip').distinct().filter(groups__has_key=exp).values_list('groups',flat=True)
        # values
        groups = []
        for i in range(len(val_queryset)):
            groups.append(val_queryset[i][exp])
        values = Counter(groups).values()
        # data
        data = {'labels': ["%.f%%" % (i / sum(values) * 100.0) for i in values],
                'series': [i for i in values]}

        return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        return HttpResponse(request.method)


# CTRLineChart view function
def line_ctr_data(request):
    """
    takes a HTTP GET request and returns a JSON response of compute_ctr LineChart data.
    :param request: HTTP
    :return: HttpResponse as json type
    """

    if request.method == 'GET':
        # get request
        exp = request.GET.get('exp')
        # queryset
        val_queryset = Experiment.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False).filter(name=exp)
        leg_queryset = Experiment.objects.filter(group__name__isnull=False).filter(name=exp)
        # elapsed_time
        started = [datetime['start_time'] for datetime in Experiment.objects.filter(name=exp).values('start_time')][0]
        today = timezone.now()
        elapsed_time = (today - started).days + 3
        # labels
        labels = [(today.date() - timezone.timedelta(days=x)).strftime('%Y-%m-%d') for x in range(elapsed_time)]
        # values
        kpi = KPI()
        values = dict()
        for label in labels:
            alist = list()
            for exp_name, group_name, act_subject in val_queryset.values_list('name', 'group__name',
                                                                              'goal__act_subject'):
                alist.append("%.2f" % (kpi.compute_ctr(exp_name, group_name, act_subject, label)))
            values[label] = alist
        # series
        series = []
        legend = [group_name for exp_name, group_name in leg_queryset.values_list('name', 'group__name')]
        for legend_idx in range(len(legend) - 1, -1, -1):
            alist = []
            for label in labels:
                result = values.get(label, {})[legend_idx]
                alist.append(result)
            series.append(alist)
        # data
        data = {'labels': labels,
                'series': series}

        return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        return HttpResponse(request.method)


# StayTimeLineChart view function
def line_time_data(request):
    """
    takes a HTTP GET request and returns a JSON response of compute_ctr LineChart data.
    :param request: HTTP
    :return: HttpResponse as json type
    """

    if request.method == 'GET':
        # get request
        exp = request.GET.get('exp')
        # queryset
        val_queryset = Experiment.objects.filter(group__name__isnull=False).filter(goal__act_subject__isnull=False).filter(name=exp)
        leg_queryset = Experiment.objects.filter(group__name__isnull=False).filter(name=exp)
        # elapsed_time
        started = [datetime['start_time'] for datetime in Experiment.objects.filter(name=exp).values('start_time')][0]
        today = timezone.now()
        elapsed_time = (today - started).days + 3
        # labels
        labels = [(today.date() - timezone.timedelta(days=x)).strftime('%Y-%m-%d') for x in range(elapsed_time)]
        # values
        kpi = KPI()
        values = dict()
        for label in labels:
            alist = list()
            for exp_name, group_name, act_subject in val_queryset.values_list('name', 'group__name',
                                                                              'goal__act_subject'):
                alist.append(kpi.compute_stayTime(exp_name, group_name, act_subject, label))
            values[label] = alist
        # series
        series = []
        legend = [group_name for exp_name, group_name in leg_queryset.values_list('name', 'group__name')]
        for legend_idx in range(len(legend) - 1, -1, -1):
            alist = []
            for label in labels:
                result = values.get(label, {})[legend_idx]
                alist.append(result)
            series.append(alist)
        # data
        data = {'labels': labels,
                'series': series}

        return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        return HttpResponse(request.method)