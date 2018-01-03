from rest_framework.test import APITestCase
from experimenter.models import Experiment, Group

class UserActionModelTests(APITestCase):

    # 같은 ip일 경우 같은 집단인가. Ramp-up은 고려하지 않음.
    def test_same_ip_same_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2)
        # 동일한 ip로 여러 번 request 보내 response로 받은 집단이 모두 같은지 비교.
        user_groups = []
        for i in range(25):
            response = self.client.post('/useractions/', {'ip': '1'}, format='json')
            user_groups.append(response.data['groups'])
        any_diff = 0
        for i in range(24):
            if user_groups[i] != user_groups[-1]:
                any_diff += 1
        self.assertEqual(any_diff, 0)

    # 다른 ip일 경우 다른 집단인가. Ramp-up은 고려하지 않음.
    def test_diff_ip_diff_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2)
        #다른 ip로 여러 번 requset 보내 response로 받은 집단이 하나라도 다른지 비교.
        user_groups = []
        for i in range(25):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            user_groups.append(response.data['groups'])
        any_diff = 0
        for i in range(24):
            if user_groups[i] != user_groups[-1]:
                any_diff += 1
        self.assertNotEqual(any_diff, 0)

