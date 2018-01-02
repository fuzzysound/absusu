from django.test import TestCase
from .models import Experiment, Group
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