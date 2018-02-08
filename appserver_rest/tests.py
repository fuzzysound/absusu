from rest_framework.test import APITestCase
from experimenter.models import Experiment, Group, Goal
from scipy.stats import chisquare
import random
import numpy as np
from experimenter.bandit import Bandit
from .models import UserAction
from django.utils import timezone
from scipy.stats import beta

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

    def create_bandits_in_test(self, experiments):
        """
        Test 내에서 생성된 실험의 bandit 애트리뷰트를 생성하는 method.
        :param experiments: Experiment 모델 인스턴스
        :return: 없음
        """
        for experiment in experiments:
            experiment.bandit = Bandit(experiment)

    def request_view_and_click_for_bandit_in_test(self, num_user, experiment, winner, odds):
        """
        Test 내에서 서버에 view와 click에 대한 request를 보내는 method.
        Bandit algorithm이 가장 좋은 arm을 제대로 찾아내는지 보기 위해 사용됨.
        :param num_user: int, request를 보내는 가상 유저의 개수
        :param experiment: Experiment 모델 인스턴스
        :param winner: str, 가장 좋은 arm에 해당하는 Group 모델 인스턴스의 name 애트리뷰트
        :param odds: dict, 가장 좋은 arm에 할당되었을 때와 그 외의 arm에 할당되었을 때 각각 유저가 클릭할 확률.
                     {'winner': float, 'loser': float}의 형식이어야 함. 각 float 값은 0과 1 사이의 값이어야 함.
        :return: 없음
        """
        assert 0 <= odds['winner'] <= 1 and 0 <= odds['loser'] <= 1, "Odds must be between 0 and 1."
        # 확률이 0-1 사이 값인지 확인
        view_action = experiment.name + '_view' # view에 대해 action 값으로 보낼 문자열 설정
        click_action = experiment.goal_set.get().act_subject + '_click' # click에 대해 action 값으로 보낼 문자열 설정
        for i in range(num_user): # 유저 수만큼
            response = self.client.post('/useractions/', {'ip': str(i), 'action': view_action}, format='json')
            # view에 대한 request 보냄
            assigned_group = response.data['groups'][experiment.name] # 할당된 집단 추출
            if assigned_group == winner: # 만약 할당된 집단이 가장 좋은 arm이면
                if random.random() < odds['winner']:
                    self.client.post('/useractions/', {'ip': str(i), 'action': click_action}, format='json')
                    # 설정한 확률로 click에 대한 request를 보냄
            else: # 할당된 집단이 그 외의 arm이면
                if random.random() < odds['loser']:
                    self.client.post('/useractions/', {'ip': str(i), 'action': click_action}, format='json')
                    # 마찬가지로 설정한 확률로 click에 대한 request를 보냄

    def update_parameters_in_test(self, experiment):
        """
        Test 내에서 실험의 bandit algorithm에서 쓰이는 베타 분포의 모수들을 업데이트하는 method.
        :param experiment: Experiment 모델 인스턴스
        :return: 없음
        """
        for i, group in enumerate(experiment.bandit.groups): # 모든 집단에 대해
            view_action = experiment.name + '_view' # view에 대해 action 값으로 받은 문자열 지정
            click_action = experiment.goal_set.get().act_subject + '_click' # click에 대해 action 값으로 받은 문자열 지정
            impressions = UserAction.objects.query_action(experiment, group, view_action,
                                                          experiment.bandit.last_update_time).count() # Impression 수 쿼리
            clicks = UserAction.objects.query_action(experiment, group, click_action,
                                                     experiment.bandit.last_update_time).count() # Click 수 쿼리
            if clicks > impressions:
                impressions = clicks # Impression 보정
            experiment.bandit.parameters[i] = tuple(map(sum, zip(experiment.bandit.parameters[i],
                                                                 (clicks, impressions - clicks)))) # 업데이트

    def update_weights_in_test(self, experiment):
        """
        Test 내에서 실험의 집단들의 weight를 업데이트하는 method.
        :param experiment: Experiment 모델 인스턴스
        :return: 없음
        """
        self.update_parameters_in_test(experiment) # 모수 업데이트
        experiment.bandit.last_update_time = timezone.now() # 최근 업데이트 시간 갱신
        new_weights = [0] * len(experiment.bandit.groups) # 새 weight 받을 list 생성
        for i in range(10000): # 10000번 실험하는 Monte-Carlo test
            thetas = [beta.rvs(a, b) for a, b in experiment.bandit.parameters] # 베타 분포로 각 집단의 이항 분포 모수 생성
            best_arm_idx = np.argmax(thetas) # 모수 값이 가장 큰 집단의 인덱스 추출
            new_weights[best_arm_idx] += 1 # 해당 집단의 weight 값에 1 추가
        for group, weight in zip(experiment.bandit.groups, new_weights): # 각 집단과 weight 값에 대해
            if weight == 0: # weight 값이 0일 경우
                group.weight = 1 # 1로 보정
            else: # 그 외에
                group.weight = weight # 각 집단의 weight 값을 새로 구한 값으로 업데이트
            group.save() # 업데이트된 값 저장

    # Bandit algorithm이 제대로 작동하는가.
    # 실제 동작에서 사용되는 모듈들이 테스트에서 제대로 동작하지 않아 부득이하게 테스트 내에 해당 모듈들의 카피를 만들어 테스트함.
    def test_bandit_algorithm_works(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit') # Bandit algorithm 사용하는 실험 생성
        Group.objects.create_test_groups(5) # 집단 5개 생성
        Goal.objects.create_test_goals(1) # 목표 1개 생성
        experiment = Experiment.objects.get() # Experiment 인스턴스 지정
        self.create_bandits_in_test([experiment]) # bandit 생성
        for i in range(5): # 총 5번 weight를 업데이트함
            self.request_view_and_click_for_bandit_in_test(1000, experiment, '2', {'winner': 0.3, 'loser': 0.2})
            # 최선의 집단을 '2'로 상정
            # 최선의 집단에서는 0.3의 확률로, 그 외 집단에서는 0.2의 확률로 클릭이 일어나도록 하여 1000명의 request를 보냄
            self.update_weights_in_test(experiment) # weight 업데이트
        group_assign_counts = [0]*5 # 각 집단에 유저가 얼마나 할당되었는지 저장할 list 생성
        for i in range(1000): # 다시 1000명의 유저에 대해
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json') # request
            assigned_group = response.data['groups'][experiment.name] # 할당된 집단 정보 추출
            group_assign_counts[int(assigned_group)] += 1 # 해당 집단의 count 값 1 추가
        best_arm_idx = np.argmax(group_assign_counts) # 가장 유저가 많이 할당된 집단 추출
        self.assertEqual(best_arm_idx, 2) # 그 집단은 2가 되어야 함

    # 여러 개의 실험이 돌아갈 때 bandit algorithm이 제대로 작동하는가. 코드 구조는 위와 대부분 같음.
    def test_bandit_algorithm_works_with_multiple_experiment(self):
        Experiment.objects.create_test_experiments(3, algorithm='bandit')
        Group.objects.create_test_groups(5)
        Goal.objects.create_test_goals(1)
        experiments = Experiment.objects.all()
        self.create_bandits_in_test(experiments)
        winners = ['1', '3', '4'] # 각 실험별로 상정하는 최선의 집단
        for i in range(5):
            for experiment, winner in zip(experiments, winners):
                self.request_view_and_click_for_bandit_in_test(1000, experiment, winner, {'winner': 0.3, 'loser': 0.2})
                self.update_weights_in_test(experiment)
        group_assign_counts_list = np.array([[0]*5]*3)
        for i in range(1000):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            for j, experiment in enumerate(experiments):
                assigned_group = response.data['groups'][experiment.name]
                group_assign_counts_list[j][int(assigned_group)] += 1
        best_arm_idx_list = []
        for group_assign_counts in group_assign_counts_list:
            best_arm_idx_list.append(np.argmax(group_assign_counts))
        self.assertEqual(best_arm_idx_list, [1, 3, 4])



    # end comment-out here