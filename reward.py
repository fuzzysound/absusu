'''
Calculate the ab test metrics
'''
from django.db import connection
import os
from functools import reduce

class KPI:
    def __init__(self):
        '''
        initialize
        '''
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "absusu.settings")

    def dictfetchall(self,cursor):
        '''
        Return all rows from a cursor as a dict"
        :param cursor: cursor
        :return: dict_cursor
        '''
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    # to check valid experiment
    def validExp(self, experiment):
        with connection.cursor() as curs:
            # check valid experiment
            sql = 'select name from experimenter_experiment;'
            curs.execute(sql)
            rows = self.dictfetchall(curs)
            experiment_list = [row['name'] for row in rows]

            if experiment not in experiment_list:
                print('Invalid experiment')
                return None
            return True

    # to caculate Click-Through Rate
    def CTR(self, experiment, group, act_subject, date):
        '''
        :param experiment: experiment to calculate
        :param group: group to calculate under the experiment
        :param act_subject: click-through rate target
        :param date: specify date to calculate CTR
        :return: click-through rate to the third decimal point of the corresponding parameters
        '''
        try:
            if self.validExp(experiment):
                with connection.cursor() as curs:
                    # check valid act_subject
                    sql = "select g.act_subject from experimenter_goal g, experimenter_experiment e \
                                    where g.experiment_id=e.id and e.name= '%s';" % (experiment)
                    curs.execute(sql)
                    rows = self.dictfetchall(curs)
                    act_subject_list = [row['act_subject'] for row in rows]

                    if act_subject not in act_subject_list:
                        print("Invalid act_subject")
                        return None

                    # Caculating CTR
                    sql = "select * from appserver_rest_useraction where json_extract(groups,'$.%s')='%s' and time < '%s' + INTERVAL 1 DAY;"\
                          % (experiment, group, date)
                    curs.execute(sql)
                    rows = self.dictfetchall(curs)

                    # initialize CTR variables
                    impressions = 0
                    clicks = 0
                    # count CTR variables for each rows
                    for row in rows:
                        if experiment in row['action'] and 'view' in row['action']:
                            impressions += 1
                        elif act_subject in row['action'] and 'click' in row['action']:
                            clicks += 1
                    ctr = clicks / impressions

                    return round(ctr, 3)

        except Exception as e:
            return 0
            # to make time series in dashboard.py reasonable, we need 0 when useraction does not occur
            # print(e)

    # Caculating how long user stay at the page
    def stayTime(self, experiment, group, act_subject, date):
        '''

        :param experiment: experiment to calculate
        :param group: group to calculate under the experiment
        :param act_subject: click-through rate target which is actually not used here, but queryset efficient
        :param date: specify date to calculate stay time
        :return: 'stay time' which describes how long user stays at the page in seconds
        '''
        try:
            if self.validExp(experiment):
                with connection.cursor() as curs:
                    # get useractions per experiment and group
                    sql = "select * from appserver_rest_useraction where json_extract(groups,'$.%s')='%s' and time < '%s' + INTERVAL 1 DAY;" \
                          % (experiment, group, date)
                    curs.execute(sql)
                    useractions = self.dictfetchall(curs)
                    time_dictionary = dict()
                    stay_time_list = list()

                    # get act_subject of the experiment what we chose
                    sql = "select act_subject from experimenter_goal g where g.id = (select id " \
                          "from experimenter_experiment e where e.name = '%s');" % (experiment)
                    curs.execute(sql)
                    act_subject_list = [x['act_subject'] for x in self.dictfetchall(curs)]

                    for action in useractions:
                        # 해당 experiment의 view action이 이루어지면 time_dictionary에 해당 시간 입력. overwrite가능.
                        if experiment in action['action'] and 'view' in action['action']:
                            time_dictionary[action['ip']] = action['time']

                        # same ip가 exp1_view - exp2_view - button2_click 상황에서 exp1_view와 button2_click 사이 시간이 계산되는 오류해결.
                        # 한 가지 실험에 여러 act_subject가 있다하더라도 동일한 페이지에서 활성화되므로 여러 button들이 있는 것은 괜찮음.
                        elif action['action'].split('_')[0] in act_subject_list and 'click' in action['action']:
                            if time_dictionary.get(action['ip'], None):
                                stay_time = action['time'] - time_dictionary.pop(action['ip'], None) # to make it memory efficient
                                stay_time_list.append(stay_time.total_seconds())

                            else:
                                pass

                    avg_stay_time = reduce(lambda x, y: x + y, stay_time_list) / len(stay_time_list)
                    return round(avg_stay_time, 3)

        except Exception as e:
            # to make StayTimeLineChart in dashboard.py reasonable, we need 0 when useraction does not occur
            return 0
            #return None

'''
# Example usage
if __name__ =="__main__":
    kpi = KPI()
    result1 = kpi.CTR('exp1','test','button1')
    result2 = kpi.CTR('exp2','test','button3')
    result3 = kpi.CTR('exp1','test','button10')
    result4 = kpi.CTR('exp3','test','button5')
    result5 = kpi.CTR('exp1', 'test3', 'button1')
    print(result1)
    print(result2)
    print(result3)
    print(result4)
    print(result5)
    del kpi
'''