from django.test import TestCase
from .models import Experiment, Group, Goal
from django.core.exceptions import ValidationError
from django.utils import timezone
import time

class ExperimentModelTests(TestCase):
    # 메소드 이름 앞에 'test_'가 붙어야 test된다는 사실 참고

    # end time이 start time보다 이른 경우
    def test_end_time_earlier_than_start_time(self):
        earlier_end_time = timezone.now() - timezone.timedelta(days=7)
        experiment = Experiment(name="experiment", end_time=earlier_end_time)
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'end_time_earlier_than_start_time')

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


class GroupModelTests(TestCase):

    # weight가 0일 경우
    def test_weight_is_zero(self):
        experiment = Experiment(name="experiment")
        group = Group(name="group", weight=0, experiment=experiment)
        with self.assertRaises(ValidationError) as cm:
            group.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'weight_is_non_positive')

    # weight가 음의 정수일 경우
    def test_weight_is_negative(self):
        experiment = Experiment(name="experiment")
        group = Group(name="group", weight=-3, experiment=experiment)
        with self.assertRaises(ValidationError) as cm:
            group.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'weight_is_non_positive')

    # control group이 0개일 경우

    # control group이 2개 이상일 경우

    # ramp up ratio가 0~100 사이의 수가 아닐 경우


class GoalModelTests(TestCase):

    def test_str_is_equal_to_name(self):
        '''
        Method `__str__` should be equal to field `name`
        '''
        experiment = Experiment.objects.create(name="exp1")
        group = Group(name="group", weight=5, experiment=experiment)
        goal = Goal.objects.create(name="button1_ctr", act_subject="button1", experiment=experiment)
        self.assertEqual(str(goal),experiment.name +' '+ goal.name)

    def test_goal_cant_have_same_name(self):
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
        from django.db import utils
        experiment1 = Experiment.objects.create(name="exp1")
        experiment2 = Experiment.objects.create(name="exp2")
        group1 = Group(name="group1",weight=5,experiment=experiment1)
        group2 = Group(name="group2", weight=5, experiment=experiment2)
        goal1 = Goal.objects.create(name="exp1_ctr", act_subject="button1", experiment=experiment1)
        with self.assertRaises(Exception) as raised:
            goal2 = Goal.objects.create(name="exp2_ctr", act_subject="button1", experiment=experiment2)
        self.assertEqual(utils.IntegrityError, type(raised.exception))