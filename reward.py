"""
Calculate the ab test metrics
"""
from django.db import connection
from functools import reduce
import os


class KPI:
    def __init__(self):
        """
        initialize
        """
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "absusu.settings")

    def dictfetchall(self, cursor):
        """
        Return all rows from a cursor as a dict"
        :param cursor: cursor
        :return: dict_cursor
        """
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def isvalid_exp(self, experiment):
        with connection.cursor() as curs:
            # check valid experiment
            sql = "select name from experimenter_experiment;"
            curs.execute(sql)
            rows = self.dictfetchall(curs)
            experiment_list = [row['name'] for row in rows]

            if experiment not in experiment_list:
                print('Invalid experiment')
                return None
            return True

    # to compute Click-Through Rate
    def compute_ctr(self, experiment, group, act_subject, date):
        """
        :param experiment: experiment to calculate
        :param group: group to calculate under the experiment
        :param act_subject: click-through rate target
        :param date: specify date to calculate compute_ctr
        :return: click-through rate to the third decimal point of the corresponding parameters
        """

        try:
            if self.isvalid_exp(experiment):
                with connection.cursor() as curs:
                    # check valid act_subject
                    sql = "select g.act_subject from experimenter_goal g, experimenter_experiment e where g.experiment_id=e.id and e.name= '%s';" \
                          % (experiment)
                    curs.execute(sql)
                    rows = self.dictfetchall(curs)
                    act_subject_list = [row['act_subject'] for row in rows]

                    if act_subject not in act_subject_list:
                        print("Invalid act_subject")
                        return None

                    # compute_ctr
                    sql = "select * from appserver_rest_useraction where json_extract(groups,'$.\"%s\"')='%s' and time < '%s' + INTERVAL 1 DAY;" \
                          % (experiment, group, date)
                    curs.execute(sql)
                    rows = self.dictfetchall(curs)

                    # initialize compute_ctr variables
                    impressions = 0
                    clicks = 0
                    # count compute_ctr variables for each rows
                    for row in rows:
                        if experiment in row['action'] and 'view' in row['action']:
                            impressions += 1
                        elif act_subject in row['action'] and 'click' in row['action']:
                            clicks += 1
                    ctr = clicks / impressions

                    return ctr

        except Exception as e:
            # print(str(e) + " in compute_ctr")
            return 0
            # to make time series i n dashboard.py reasonable, we need 0 when useraction does not occur

    # to compute Stay Time
    def compute_stayTime(self, experiment, group, act_subject, date):
        '''
        :param experiment: experiment to calculate
        :param group: group to calculate under the experiment
        :param act_subject: click-through rate target which is actually not used here, but queryset efficient
        :param date: specify date to calculate stay time
        :return: 'stay time' which describes how long user stays at the page in seconds
        '''
        try:
            if self.isvalid_exp(experiment):
                with connection.cursor() as curs:
                    # get useractions per experiment and group
                    sql = "select * from appserver_rest_useraction where json_extract(groups,'$.\"%s\"')='%s' and time < '%s' + INTERVAL 1 DAY;" \
                          % (experiment, group, date)
                    curs.execute(sql)
                    useractions = self.dictfetchall(curs)
                    time_dictionary = dict()
                    stay_time_list = list()

                    # return experiment, group, act_subject, date
                    # # get act_subject of the experiment what we chose
                    # sql = "select act_subject from experimenter_goal g where g.id = (select id " \
                    #       "from experimenter_experiment e where e.name = '%s');" % (experiment)
                    # curs.execute(sql)
                    # act_subject = [x['act_subject'] for x in self.dictfetchall(curs)][0]

                    for action in useractions:
                        # view
                        # 해당 experiment에 대한 'view' action이 이루어지면 time_dictionary에 해당 시간 입력. overwrite가능.
                        if experiment in action['action'] and 'view' in action['action']:
                            time_dictionary[action['ip']] = action['time']

                        # leave
                        # same ip가 exp1_view - exp2_view - button2_click 상황에서 exp1_view와 button2_click 사이 시간이 계산되는 오류해결
                        # 한 가지 실험에 여러 act_subject가 있다하더라도 동일한 페이지에서 활성화되므로 여러 button들이 있는 것은 괜찮음
                        # 추후 수정
                        elif act_subject in action['action'] and 'leave' in action['action']:
                            if time_dictionary.get(action['ip'], None):
                                stay_time = action['time'] - time_dictionary.pop(action['ip'], None) # to make it memory efficient
                                stay_time = stay_time.total_seconds()
                                if not stay_time < 0.5: # 새로고침에 따른 오류방지
                                    stay_time_list.append(stay_time)

                            else:
                                # to prevent revisitor comes first in useractions.
                                try:
                                    stay_time

                                except NameError:
                                    stay_time = None

                                if stay_time:
                                    # Assume that the user who revisits the page via back or backward button would spend half of previous stay time
                                    stay_time = stay_time / 2
                                    stay_time_list.append(stay_time)
                    # return time_dictionary
                    avg_stay_time = reduce(lambda x, y: x + y, stay_time_list) / len(stay_time_list)
                    return round(avg_stay_time, 3)

        except Exception as e:
            # to make StayTimeLineChart in dashboard.py reasonable, we need 0 when useraction does not occur
            return 0