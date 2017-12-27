from django.test import TestCase
from .models import Experiment
from django.core.exceptions import ValidationError
from django.utils import timezone

class ExperimentModelTests(TestCase):

    # 메소드 이름 앞에 'test_'가 붙어야 test된다는 사실 참고

    def test_name_is_blank(self):
        experiment = Experiment(name="", groups=['A', 'B'], ratio=[0.5, 0.5])
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'name_is_blank')

    def test_num_of_groups_less_than_two(self):
        experiment = Experiment(name="experiment", groups=['A'], ratio=[1])
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'num_of_groups_less_than_two')

    def test_groups_ratio_length_does_not_match(self):
        experiment = Experiment(name="experiment", groups=['A', 'B', 'C'], ratio=[0.5, 0.5])
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'groups_ratio_length_does_not_match')

    def test_sum_of_ratio_is_not_valid(self):
        experiment = Experiment(name="experiment", groups=['A', 'B'], ratio=[0.5, 0.1])
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'sum_of_ratio_is_not_valid')

    def test_start_time_earlier_than_now(self):
        earlier_start_time = timezone.now() - timezone.timedelta(days=7)
        experiment = Experiment(name="experiment", groups=['A', 'B'], ratio=[0.5, 0.5], start_time=earlier_start_time)
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'start_time_earlier_than_now')

    def test_end_time_earlier_than_start_time(self):
        earlier_end_time = timezone.now() - timezone.timedelta(days=7)
        experiment = Experiment(name="experiment", groups=['A', 'B'], ratio=[0.5, 0.5], end_time=earlier_end_time)
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'end_time_earlier_than_start_time')