from rest_framework.test import APITestCase
from experimenter.models import Experiment, Group
from scipy.stats import chisquare

class UserActionModelTests(APITestCase):

    # 같은 ip일 경우 같은 집단인가. Ramp-up은 고려하지 않음.
    def test_same_ip_same_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2, ramp_up=False)
        # 동일한 ip로 여러 번 request 보내 response로 받은 집단이 모두 같은지 비교.
        user_groups = [] # 각각의 request에 대해 response로 받은 집단 정보가 담길 리스트.
        for i in range(25): # 25번 request를 보낸다
            response = self.client.post('/useractions/', {'ip': '1'}, format='json') # 임의의 ip로 request 보냄
            user_groups.append(response.data['groups']) # response에서 집단 정보를 추출해 user_groups 리스트에 추가
        any_diff = 0 # 서로 다른 그룹의 개수가 담길 변수
        for i in range(24):
            if user_groups[i] != user_groups[-1]: # 리스트의 첫 번째 요소와 나머지를 하나씩 비교한다
                any_diff += 1 # 다른 것이 있을 때마다 기록
        self.assertEqual(any_diff, 0) # 리스트의 모든 요소가 모두 같은가

    # 다른 ip일 경우 다른 집단인가. Ramp-up은 고려하지 않음.
    def test_diff_ip_diff_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2, ramp_up=False)
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

    # If test takes too long, start comment-out here

    # 의도한 비율대로 집단이 배정되는가 (ramp-up X)
    def test_weight_works(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(10, ramp_up=False)
        group_assign_counts = [0]*10 # 각 그룹마다 할당된 유저의 수를 나타낼 리스트
        for i in range(10000):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            assigned_group = response.data['groups']['0']
            group_assign_counts[int(assigned_group)] += 1 # 유저가 어느 집단에 할당되었는지 센다
        expected = [1000]*10 # 의도한 분포
        chi, p = chisquare(group_assign_counts, expected) # 실제 분포가 의도한 분포와 얼마나 다른지 카이제곱 검정
        self.assertGreaterEqual(p, 0.1) # 이것이 두 분포가 같음을 보장하진 않음. 다만 최소한의 유사성을 보장하기 위한 것임.


    # 의도한 비율대로 집단이 배정되는가 (ramp-up O)
    def test_ramp_up_works(self):
        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(10, ramp_up=True, ramp_up_percent=10) # 여기선 ramp up을 사용하는 것으로 설정
        group_assign_counts = [0]*10
        for i in range(10000):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            assigned_group = response.data['groups']['0']
            group_assign_counts[int(assigned_group)] += 1
        expected = [9100] + [100]*9 # ramp up percent가 10%이므로 실험 집단에는 1000명의 10%인 100명만 배정된다
        chi, p = chisquare(group_assign_counts, expected)
        self.assertGreaterEqual(p, 0.1)

    # end comment-out here