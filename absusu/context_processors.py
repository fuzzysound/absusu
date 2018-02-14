""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/absusu/context_processors.py
"""
### 관리자 페이지 드롭다운 메뉴의 항목을 제공하는 모듈
def dropdown_menus(request):
    menus = [
        {'name': 'Experiment',
         'sub_menus': [
             {'name': 'Create & Modify', 'url': '/admin/experimenter/experiment'},
             {'name': 'Dashboard', 'url': '/admin/dashboard/absusu'}
         ]},
        {'name': 'Authorization',
         'sub_menus': [
             {'name': 'Groups', 'url': '/admin/auth/group'},
             {'name': 'Users', 'url': '/admin/auth/user'}
         ]}
    ]
    return {'dropdown_menus': menus}