from django.db import connection
import os

class KPI:
    def __init__(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "absusu.settings")

    def dictfetchall(self,cursor):
        '''
        "Return all rows from a cursor as a dict"
        :param cursor: cursor
        :return: dict_cursor
        '''
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def CTR(self, experiment, group, act_subject):
        '''
        :param experiment: experiment to calculate
        :param group: group to calculate under the experiment
        :param act_subject: click-through rate target
        :return: click-through rate under those conditions
        '''
        try:
            with connection.cursor() as curs:
                # check valid act_subject
                act_subject_list = []
                sql = "select g.act_subject from experimenter_goal g, experimenter_experiment e \
                                where g.experiment_id=e.id and e.name= '%s';" % (experiment)
                curs.execute(sql)
                rows = self.dictfetchall(curs)
                for row in rows:
                    act_subject_list.append(row['act_subject'])

                if act_subject not in act_subject_list:
                    print("Invalid act_subject")
                    return None

                #caculate CTR
                sql = "select * from appserver_rest_useraction where json_extract(groups,'$.%s')='%s';" % (experiment, group)
                curs.execute(sql)
                rows = self.dictfetchall(curs)

                impressions = 0
                clicks = 0
                for row in rows:
                    if experiment in row['action'] and 'view' in row['action']:
                        impressions += 1
                    elif act_subject in row['action'] and 'click' in row['action']:
                        clicks += 1
                ctr = clicks / impressions

                return ctr

        except Exception as e:
            print(e)

'''
#example
if __name__ =="__main__":
    kpi = KPI()
    result1 = kpi.CTR('exp1','test','button1')
    result2 = kpi.CTR('exp1','control','button1')
    result3 = kpi.CTR('exp1','test','button2')
    result4 = kpi.CTR('exp2','test','button2')
    result5 = kpi.CTR('exp2', 'control', 'button2')
    print(result1)
    print(result2)
    print(result3)
    print(result4)
    print(result5)
    del kpi
'''