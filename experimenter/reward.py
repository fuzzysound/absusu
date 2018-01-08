import pymysql

conn = pymysql.connect(host='localhost',
                       user='absusu',
                       password='absusu',
                       db='absusu_log',
                       charset='utf8')

def CTR(experiment, group, act_subject):
    try:
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = "select * from appserver_rest_useraction where json_extract(groups,'$.%s')='%s';" % (experiment, group)
        curs.execute(sql)
        rows = curs.fetchall()

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

    finally:
        conn.close()

'''
#for test
if __name__ =="__main__":
    result = CTR('exp1','test','button1')
    print(result)
'''