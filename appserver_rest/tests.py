from django.test import TestCase
from .models import UserAction
from experimenter.models import Experiment, Group

class UserActionModelTests(TestCase):

    # 같은 ip일 경우 같은 집단인가. Ramp-up은 고려하지 않음.
    def test_same_ip_same_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2)
        # 동일한 ip를 가진 여러 개의 useraction 생성해 집단이 모두 같은지 비교.
        useractions = []
        for i in range(25):
            useractions.append(UserAction(ip='1'))
            useractions[-1].save()
        any_diff = 0
        for i in range(24):
            if useractions[i].groups != useractions[-1].groups:
                any_diff += 1
        self.assertEqual(any_diff, 0)

    # 다른 ip일 경우 다른 집단인가. Ramp-up은 고려하지 않음.
    def test_diff_ip_diff_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2)
        # 다른 ip를 가진 여러 개의 useraction 생성해 집단이 하나라도 다른지 비교.
        useractions = []
        for i in range(25):
            useractions.append(UserAction(ip=str(i)))
            useractions[-1].save()
        any_diff = 0
        for i in range(24):
            if useractions[i].groups != useractions[-1].groups:
                any_diff += 1
        self.assertNotEqual(any_diff, 0)