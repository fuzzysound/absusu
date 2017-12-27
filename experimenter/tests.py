from django.test import TestCase
from .models import Experiment, Group
from django.core.exceptions import ValidationError
from django.utils import timezone

class ExperimentModelTests(TestCase):

    # 메소드 이름 앞에 'test_'가 붙어야 test된다는 사실 참고

    def test_end_time_earlier_than_start_time(self):
        earlier_end_time = timezone.now() - timezone.timedelta(days=7)
        experiment = Experiment(name="experiment", end_time=earlier_end_time)
        with self.assertRaises(ValidationError) as cm:
            experiment.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'end_time_earlier_than_start_time')


class GroupModelTests(TestCase):

    def test_weight_is_non_positive(self):
        experiment = Experiment(name="experiment")
        group = Group(name="group", weight=0, experiment=experiment)
        with self.assertRaises(ValidationError) as cm:
            group.clean()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 'weight_is_non_positive')