from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Experiment, Group, Goal
from .forms import GroupAdminForm
import time
from reward import KPI
import random


class ExperimentModelTests(TestCase):
    # 메소드 이름 앞에 'test_'가 붙어야 test된다는 사실 참고

    # end time이 start time보다 이른 경우
    def test_end_time_earlier_than_start_time(self):
        earlier_end_time = timezone.now() - timezone.timedelta(days=7) # 시작시간을 임의로 현재시각보다 이르게 설정
        experiment = Experiment(name="experiment", end_time=earlier_end_time) # 시작시간이 현재시각보다 이른 Experiment 인스턴스 생성
        with self.assertRaises(ValidationError) as cm: # 에러를 관리하는 context manager 생성
            experiment.clean() # validate
        the_exception = cm.exception # 예외 추출
        self.assertEqual(the_exception.code, 'end_time_earlier_than_start_time') # 예외 코드가 미리 설정한 것과 일치하는지 검증

    # 실제로 실험이 active할 때 active_now() 값이 True인가
    def test_active_now_true(self):
        experiment = Experiment(name='experiment')
        self.assertIs(experiment.active_now(), True)

    # 실제로 실험이 active하지 않을 때 active_now() 값이 False인가
    def test_active_now_false(self):
        # end_time을 현재시간보다 아주 약간 나중으로 설정해, 실험이 생성되자마자 거의 바로 끝나도록 함
        experiment = Experiment(name='experiment', end_time=timezone.now()+timezone.timedelta(seconds=0.0000001))
        time.sleep(0.00000011) # 만약을 위해 아주 약간 pause
        self.assertIs(experiment.active_now(), False)

    # assignment update interval이 0일 경우
    def test_assignment_update_interval_is_zero(self):
        experiment = Experiment(name="experiment", algorithm='bandit', assignment_update_interval=0)
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'assignment_update_interval_not_positive')

    # assignment update interval이 음수일 경우
    def test_assignment_update_interval_is_negative(self):
        experiment = Experiment(name="experiment", algorithm='bandit', assignment_update_interval=-24)
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'assignment_update_interval_not_positive')


class GroupModelTests(TestCase):

    # weight가 0일 경우
    def test_weight_is_zero(self):
        experiment = Experiment(name="experiment") # 임의의 Experiment 인스턴스 생성
        group = Group(name="group", weight=0, experiment=experiment) # weight가 0인 Group 인스턴스 생성
        with self.assertRaises(ValidationError) as cm: # context manager
            group.clean() # validate
        the_exception = cm.exception # 예외 추출
        self.assertEqual(the_exception.code, 'weight_is_non_positive') # 예외 코드가 미리 설정한 것과 일치하는지 검증

    # weight가 음의 정수일 경우, 코드 구조는 위와 같음
    def test_weight_is_negative(self):
        experiment = Experiment(name="experiment")
        group = Group(name="group", weight=-3, experiment=experiment)
        with self.assertRaises(ValidationError) as cm:
            group.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'weight_is_non_positive')

    # ramp up percent가 0보다 작을 경우, 코드 구조는 위와 같음
    def test_ramp_up_percent_is_less_than_zero(self):
        experiment = Experiment(name="experiment")
        group = Group(name="group", weight=1, experiment=experiment, ramp_up='manual', ramp_up_percent=-30)
        with self.assertRaises(ValidationError) as cm:
            group.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'ramp_up_percent_is_not_valid')

    # ramp up percent가 100보다 클 경우, 코드 구조는 위와 같음
    def test_ramp_up_percent_is_greater_than_a_hundred(self):
        experiment = Experiment(name="experiment")
        group = Group(name="group", weight=1, experiment=experiment, ramp_up='manual', ramp_up_percent=130)
        with self.assertRaises(ValidationError) as cm:
            group.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'ramp_up_percent_is_not_valid')

    # ramp up 종료시간이 실험 시작시간보다 이전일 경우
    def test_ramp_up_end_time_before_experiment_start_time(self):
        earlier_ramp_up_end_time = timezone.now() - timezone.timedelta(days=7) # 실험 시작시간보다 일주일 전으로 설정
        Experiment.objects.create(name='experiment') # 실험 1개 생성
        experiment = Experiment.objects.all() # 실험을 queryset으로 불러옴
        group_data = {'name': 'group', 'ramp_up': 'automatic', 'ramp_up_end_time': earlier_ramp_up_end_time,
                      'experiment': experiment} # form에 집어넣을 데이터
        group_form = GroupAdminForm(group_data) # group form 인스턴스 생성. Validation이 form에서 일어나도록 했으므로.
        group_form.is_valid() # cleaned_data를 생성하기 위한 호출. 그 외에 아무 일도 일어나지 않음.
        with self.assertRaises(ValidationError) as cm:
            group_form.clean() # validate
        the_exception = cm.exception # 예외 추출
        self.assertEqual(the_exception.code, 'ramp_up_end_time_not_valid')

    # ramp up 종료시간이 실험 종료시간보다 이후일 경우, 코드 구조는 위와 같음
    def test_ramp_up_end_time_after_experiment_end_time(self):
        later_ramp_up_end_time = timezone.now() + timezone.timedelta(days=14) # 실험 종료시간보다 일주일 후로 설정
        Experiment.objects.create(name='experiment')
        experiment = Experiment.objects.all()
        group_data = {'name': 'group', 'ramp_up': 'automatic', 'ramp_up_end_time': later_ramp_up_end_time,
                      'experiment': experiment}
        group_form = GroupAdminForm(group_data)
        group_form.is_valid()
        with self.assertRaises(ValidationError) as cm:
            group_form.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'ramp_up_end_time_not_valid')


class GoalModelTests(TestCase):

    def test_str_is_equal_to_name(self):
        """
        `__str__` must be equal to name field
        """
        experiment = Experiment.objects.create(name="exp1")
        group = Group(name="group", weight=5, experiment=experiment)
        goal = Goal.objects.create(name="button1_ctr", act_subject="button1", experiment=experiment)
        self.assertEqual(str(goal),experiment.name +' '+ goal.name)

    def test_goal_cant_have_same_name(self):
        """
        name field of each Goal model object must be unique
        """
        from django.db import utils
        experiment1 = Experiment.objects.create(name="exp1")
        experiment2 = Experiment.objects.create(name="exp2")
        group1 = Group(name="group1",weight=5,experiment=experiment1)
        group2 = Group(name="group2", weight=5, experiment=experiment2)
        goal1 = Goal.objects.create(name="button1_ctr", act_subject="button1", experiment=experiment1)
        with self.assertRaises(Exception) as raised:
            goal2 = Goal.objects.create(name="button1_ctr", act_subject="button2", experiment=experiment2)
        self.assertEqual(utils.IntegrityError, type(raised.exception))

    def test_goal_cant_have_same_act_subject(self):
        """
        act_subject field of each Goal model object must be unique
        """
        from django.db import utils
        experiment1 = Experiment.objects.create(name="exp1")
        experiment2 = Experiment.objects.create(name="exp2")
        group1 = Group(name="group1",weight=5,experiment=experiment1)
        group2 = Group(name="group2", weight=5, experiment=experiment2)
        goal1 = Goal.objects.create(name="exp1_ctr", act_subject="button1", experiment=experiment1)
        with self.assertRaises(Exception) as raised:
            goal2 = Goal.objects.create(name="exp2_ctr", act_subject="button1", experiment=experiment2)
        self.assertEqual(utils.IntegrityError, type(raised.exception))


class KPITests(TestCase):

    # Group 간 클릭하는 비율이 다른 경우 'compute_ctr'이 이를 잘 비교하는지 검증
    def test_ctr_calcuation(self):

        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(2)
        Goal.objects.create_test_goals()

        for ip in range(50):
            response = self.client.post('/useractions/', {'ip': str(ip), 'action': '0_view'}, format='json')

            if response.data['groups']['0'] == '0':
                if random.random() < 0.9:
                    self.client.post('/useractions/', {'ip': str(ip), 'action': '0_click'}, format='json')
            else:
                if random.random() < 0.3:
                    self.client.post('/useractions/', {'ip': str(ip), 'action': '0_click'}, format='json')

        kpi = KPI()
        ctr_0 = kpi.compute_ctr('0', '0', '0', timezone.now().date())
        ctr_1 = kpi.compute_ctr('0', '1', '0', timezone.now().date())
        self.assertGreater(ctr_0, ctr_1)

    # Group 간 페이지에 머무는 체류시간이 다른 경우 'compute_staytime'이 이를 잘 비교하는지 검증
    def test_staytime_calcuation(self):

        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(2)
        Goal.objects.create_test_goals()

        for ip in range(50):
            response = self.client.post('/useractions/', {'ip': str(ip), 'action': '0_view'}, format='json')

            if response.data['groups']['0'] == '0':
                time.sleep(random.uniform(1.0, 3.0))
                self.client.post('/useractions/', {'ip': str(ip), 'action': '0_leave'}, format='json')
            else:
                time.sleep(random.uniform(0.1, 1.0))
                self.client.post('/useractions/', {'ip': str(ip), 'action': '0_leave'}, format='json')

        kpi = KPI()
        staytime_0 = kpi.compute_stayTime('0', '0', '0', timezone.now().date())
        staytime_1 = kpi.compute_stayTime('0', '1', '0', timezone.now().date())
        self.assertGreater(staytime_0, staytime_1)