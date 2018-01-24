'''
Calculate the ab test metrics
'''
from django.db import connection
import os

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

    # date: to specify time period
    def CTR(self, experiment, group, act_subject, date):
        '''
        :param experiment: experiment to calculate
        :param group: group to calculate under the experiment
        :param act_subject: click-through rate target
        :param date: specify date to calculate CTR
        :return: click-through rate to the third decimal point of the corresponding parameters
        '''
        try:
            with connection.cursor() as curs:
                # check valid experiment
                sql = 'select name from experimenter_experiment;'
                curs.execute(sql)
                rows = self.dictfetchall(curs)
                experiment_list = [row['name'] for row in rows]

                if experiment not in experiment_list:
                    print('Invalid experiment')
                    return None

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