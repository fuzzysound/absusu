""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/appserver_rest/tests.py
"""
from rest_framework.test import APITestCase
from experimenter.models import Experiment, Group, Goal
from scipy.stats import chisquare, beta, norm
from scipy.optimize import minimize
import random
import numpy as np
from experimenter.bandit import Bandit
from .models import UserAction
from experimenter.bandit import *
from django.utils import timezone
import time
import pymc3 as pm

class UserActionModelTests(APITestCase):

    # 같은 ip일 경우 같은 집단인가. Ramp-up은 고려하지 않음.
    def test_same_ip_same_group(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(2)
        Group.objects.create_test_groups(2)
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

    # If test takes too long, start comment-out here

    # 의도한 비율대로 집단이 배정되는가 (ramp-up X)
    def test_weight_works(self):
        # 임의의 실험과 집단 생성
        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(10)
        group_assign_counts = [0]*10 # 각 그룹마다 할당된 유저의 수를 나타낼 리스트
        for i in range(10000):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            assigned_group = response.data['groups']['0']
            group_assign_counts[int(assigned_group)] += 1 # 유저가 어느 집단에 할당되었는지 센다
        expected = [1000]*10 # 의도한 분포
        chi, p = chisquare(group_assign_counts, expected) # 실제 분포가 의도한 분포와 얼마나 다른지 카이제곱 검정
        self.assertGreaterEqual(p, 0.1) # 이것이 두 분포가 같음을 보장하진 않음. 다만 최소한의 유사성을 보장하기 위한 것임.


    # 의도한 비율대로 집단이 배정되는가 (manual ramp up)
    def test_ramp_up_works(self):
        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(10, ramp_up='manual', ramp_up_percent=10) # 여기선 maunal ramp up을 사용하는 것으로 설정
        group_assign_counts = [0]*10
        for i in range(10000):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            assigned_group = response.data['groups']['0']
            group_assign_counts[int(assigned_group)] += 1
        expected = [9100] + [100]*9 # ramp up percent가 10%이므로 실험 집단에는 1000명의 10%인 100명만 배정된다
        chi, p = chisquare(group_assign_counts, expected)
        self.assertGreaterEqual(p, 0.1)

    # automatic ramp up이 제대로 작동하는가
    def test_automatic_ramp_up_works(self):
        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(2, ramp_up='automatic', # automatic ramp up을 사용하는 것으로 설정
                                         ramp_up_end_time=timezone.now()+timezone.timedelta(minutes=2)) # 2분 동안 사용
        group_assign_counts_list = np.array([[0]*2]*3) # 세 번에 걸쳐 유저 할당 수를 볼 것이므로 2*3 array를 만든다
        for i in range(3): # 세 번에 걸쳐
            for j in range(100): # 100명 분의 request를 보냄
                response = self.client.post('/useractions/', {'ip': str(j)}, format='json')
                assigned_group = response.data['groups']['0']
                group_assign_counts_list[i][int(assigned_group)] += 1
            if i < 2: # 마지막 횟수를 제외하고
                time.sleep(60) # 다음 횟수 전까지 1분을 쉼
        exp_group_assign_counts_list = list(zip(*group_assign_counts_list))[1] # 실험 집단의 유저 할당 수만 추출
        self.assertGreaterEqual(exp_group_assign_counts_list[1], exp_group_assign_counts_list[0])
        self.assertGreaterEqual(exp_group_assign_counts_list[2], exp_group_assign_counts_list[1])
        # 시간이 지날수록 실험 집단의 유저 할당 수가 늘어나야 함

    # 아래는 bandit algorithm에 관한 메소드와 테스트들
    # 실제 동작에서 사용되는 모듈들이 테스트에서 제대로 동작하지 않아 부득이하게 테스트 내에 해당 모듈들의 카피를 만들어 테스트함.
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

    def request_view_and_leave_for_bandit_in_test(self, num_user, experiment, winner, times):
        """
        Test 내에서 서버에 view와 leave에 대한 request를 보내는 method.
        Bandit algorithm이 가장 좋은 arm을 제대로 찾아내는지 보기 위해 사용됨.
        :param num_user: int, request를 보내는 가상 유저의 개수
        :param experiment: Experiment 모델 인스턴스
        :param winner: str, 가장 좋은 arm에 해당하는 Group 모델 인스턴스의 name 애트리뷰트
        :param times: dict, 가장 좋은 arm에 할당되었을 때와 그 외의 arm에 할당되었을 때 각각 유저가 페이지에 머무를 평균 시간(초).
                     {'winner': float, 'loser': float}의 형식이어야 함. 각 float 값은 0 이상의 값이어야 함.
        :return: 없음
        """
        assert times['winner'] > 0 and times['loser'] > 0, "Times must be positive."
        # 시간이 0 이상의 값인지 확인
        view_action = experiment.name + '_view'  # view에 대해 action 값으로 보낼 문자열 설정
        leave_action = experiment.goal_set.get().act_subject + '_leave'  # leave에 대해 action 값으로 보낼 문자열 설정
        for i in range(num_user):  # 유저 수만큼
            response = self.client.post('/useractions/', {'ip': str(i), 'action': view_action}, format='json')
            # view에 대한 request 보냄
            assigned_group = response.data['groups'][experiment.name]  # 할당된 집단 추출
            if assigned_group == winner:  # 만약 할당된 집단이 가장 좋은 arm이면
                winner_time = times['winner'] # 가장 좋은 arm의 평균 체류시간 추출
                time_in_page = norm.rvs(winner_time, (winner_time / 2)**2) # 표준편차가 평균의 제곱근인 정규분포에서 체류시간 추출
                time.sleep(time_in_page) # 체류시간만큼 일시정지
                self.client.post('/useractions/', {'ip': str(i), 'action': leave_action}, format='json')
                # leave에 대한 request를 보냄
            else:  # 할당된 집단이 그 외의 arm이면
                loser_time = times['loser'] # 안 좋은 arm의 평균 체류시간 추출
                time_in_page = norm.rvs(loser_time, loser_time**2) # 표준편차가 평균의 제곱근인 정규분포에서 체류시간 추출
                time.sleep(time_in_page) # 체류시간만큼 일시정지
                self.client.post('/useractions/', {'ip': str(i), 'action': leave_action}, format='json')
                # 마찬가지로 leave에 대한 request를 보냄

    def get_new_successes_and_failures_in_test(self, experiment, group):
        """
        테스트 내에서 이전 업데이트 이후 새로 기록된 성공과 실패 횟수를 반환하는 method
        :param experiment: Experiment 인스턴스
        :param group: Group 인스턴스
        :return: tuple, (성공 횟수, 실패 횟수)
        """
        if experiment.goal_set.get().KPI == 'clicks': # KPI가 CTR일 경우의 계산
            view_action = experiment.name + '_view' # view에 대해 action 값으로 받은 문자열 지정
            click_action = experiment.goal_set.get().act_subject + '_click' # click에 대해 action 값으로 받은 문자열 지정
            impressions = UserAction.objects.query_action(experiment, group, view_action,
                                                          experiment.bandit.last_update_time).count() # Impression 수 쿼리
            clicks = UserAction.objects.query_action(experiment, group, click_action,
                                                     experiment.bandit.last_update_time).count() # Click 수 쿼리

            self.last_update_time = timezone.now()  # 최근 업데이트 시간 갱신
            if clicks > impressions:
                impressions = clicks # Impression 보정
            return clicks, impressions - clicks
        else: # 등록되지 않은 KPI일 경우
            raise ValueError("Unknown KPI:", self.goal.KPI)

    def get_new_rewards_in_test(self, experiment, group):
        """
        테스트 내에서 이전 업데이트 이후 새로 기록된 보상(reward)을 반환하는 method
        :param experiment: Experiment 인스턴스
        :param group: Group 인스턴스
        :return: 모든 보상
        """
        if experiment.goal_set.get().KPI == 'time': # KPI가 체류시간일 경우의 계산
            view_action = experiment.name + '_view' # view에 대해 action 값으로 받은 문자열 지정
            leave_action = experiment.goal_set.get().act_subject + '_leave' # leave에 대해 action 값으로 받은 문자열 지정
            time_on_page_list = [] # 체류시간이 들어갈 list
            earliest_latest_leave_time = experiment.bandit.last_update_time
            leaves = UserAction.objects.query_action(experiment, group, leave_action, experiment.bandit.last_update_time)
            # leave_action이 포함된 모든 로그를 가져옴
            distinct_ip_list = set(leaves.values_list('ip')) # 고유한 ip 주소 추출
            for ip in distinct_ip_list: # 각각의 ip 주소에 대해
                leaves_of_the_ip = leaves.filter(ip__exact=ip[0]).order_by('time') # 이 ip가 남긴 leave를 시간순 정렬
                last_leave_time = experiment.bandit.last_update_time
                # 가장 처음의 leave는 이전 leave가 없으므로, 이 때의 초기값을 last_update_time으로 줌
                for leave in leaves_of_the_ip: # 이 ip 주소의 모든 leave에 대해
                    views = UserAction.objects.filter(ip__exact=ip[0]).query_action(experiment, group, view_action,
                                                            last_leave_time, leave.time).order_by('-time')
                    # leave와 그 이전 leave 사이의 모든 view를 최신순으로 정렬
                    if views: # view가 존재할 경우
                        latest_view_time = views[0].time # 그 중 가장 최신의 view를 추출
                        time_on_page = leave.time - latest_view_time # 체류시간 계산
                        time_on_page_list.append(time_on_page.seconds*1000 + time_on_page.microseconds/1000)
                        # 밀리세컨드 단위로 환산해 리스트에 추가. 테스트에 적은 시간을 들이기 위해 밀리세컨드를 사용함.
                    else: # view가 없을 경우
                        time_on_page = (leave.time - last_leave_time) / 2 # 임의로 체류시간 계산
                        time_on_page_list.append(time_on_page.seconds*1000 + time_on_page.microseconds/1000)
                        # 리스트에 추가
                    last_leave_time = leave.time
                    # last_leave_time 값은 계속 덮어씌워져 결국에는 가장 나중의 leave의 시간 값이 됨
                if last_leave_time < earliest_latest_leave_time:
                    earliest_latest_leave_time = last_leave_time # 모든 이용자의 마지막 leave 중 가장 이른 것으로 지정
            experiment.bandit.last_update_time = earliest_latest_leave_time # 그 값으로 last_update_time을 업데이트
            return time_on_page_list
        else: # 등록되지 않은 KPI일 경우
            raise ValueError("Unknown KPI:", self.goal.KPI)

    def update_beta_dist_parameters_in_test(self, experiment):
        """
        Test 내에서 실험의 bandit algorithm에서 쓰이는 베타 분포의 모수들을 업데이트하는 method.
        :param experiment: Experiment 모델 인스턴스
        :return: 없음
        """
        for i, group in enumerate(experiment.bandit.groups): # 모든 집단에 대해
            successes, failures = self.get_new_successes_and_failures_in_test(experiment, group) # 새로운 성공과 실패 횟수 얻기
            experiment.bandit.parameters[i] = tuple(map(sum, zip(experiment.bandit.parameters[i],
                                                                 (successes, failures)))) # 업데이트
    def update_model_in_test(self, experiment):
        """
        Test 내에서 실험의 bandit algorithm에서 쓰이는 베이지언 모델을 업데이트하는 method.
        :param experiment: Experiment 모델 인스턴스
        :return: 없음
        """
        rewards = [] # 관측값(보상)이 담길 리스트
        dummy_coded_group_variables = [] # 더미코딩된 변수 값이 담길 리스트
        for i, group in enumerate(experiment.bandit.groups): # 모든 집단에 대해
            rewards_of_the_group = self.get_new_rewards_in_test(experiment, group) # 새로운 보상 리스트 얻기
            dummy = [0]*len(experiment.bandit.groups)
            dummy[i] += 1 # 이 집단에 대한 더미코딩된 변수 값 생성
            dummy_coded_group_variable = [dummy]*len(rewards_of_the_group) # 이 값을 보상 개수만큼 만듬
            rewards += rewards_of_the_group # 리스트에 추가
            dummy_coded_group_variables += dummy_coded_group_variable # 리스트에 추가
        dummy_coded_group_variables = list(zip(*dummy_coded_group_variables))
        # 열과 행을 바꾸어주어 아래에서 모델에 추가할 수 있도록 함.
        # shape가 (집단 개수, 보상 개수)에서 (보상 개수, 집단 개수)로 바뀜
        experiment.bandit.model = pm.Model() # 베이지언 모델을 새로 생성해 모델을 새로 정의할 수 있도록 함
        with experiment.bandit.model:
            alpha = from_posterior('alpha', experiment.bandit.trace['alpha']) # intercept 업데이트
            beta = []
            for i in range(len(experiment.bandit.groups)):
                beta.append(from_posterior('beta'+str(i), experiment.bandit.trace['beta'+str(i)]))
                # 각각의 coefficient 업데이트
            sigma = from_posterior_halfnormal('sigma', experiment.bandit.trace['sigma'])
            mu = alpha
            if rewards:
                for i in range(len(beta)):
                    mu += beta[i]*dummy_coded_group_variables[i]
                    # for loop을 이용해 mu 안에 각 coefficient와 변수를 곱한 것을 집어넣음.
            Y_obs = pm.Normal('Y_obs', mu=mu, sd=sigma, observed=rewards) # 모델 정의
            experiment.bandit.trace = pm.sample(1000, cores=1) # 1000개의 샘플 추출.

    def get_new_weights_with_binary_reward_in_test(self, experiment):
        """
        Test 내에서 binary type의 KPI를 사용했을 경우 새 weight 값을 얻는 method
        :param experiment: Experiment 모델 인스턴스
        :return: list, 각 집단들의 새로운 weight 값
        """
        new_weights = [0] * len(experiment.bandit.groups) # 새 weight 받을 list 생성
        thetas_list = [] # 모든 theta 값을 담을 리스트. Auto termination을 하기 위함.
        for i in range(1000): # 1000번 실험하는 Monte-Carlo test
            thetas = [beta.rvs(a, b) for a, b in experiment.bandit.parameters] # 베타 분포로 각 집단의 이항 분포 모수 생성
            thetas_list.append(thetas) # 리스트에 추가
            best_arm_idx = np.argmax(thetas) # 모수 값이 가장 큰 집단의 인덱스 추출
            new_weights[best_arm_idx] += 1 # 해당 집단의 weight 값에 1 추가
        if experiment.auto_termination: # auto termination을 사용할 경우
            best_arm_idx = np.argmax(new_weights) # 최선의 집단의 인덱스 추출
            self.check_auto_termination(experiment, thetas_list, best_arm_idx) # 실험 종료 여부 확인
        return new_weights

    def get_new_weights_with_continuous_reward_in_test(self, experiment):
        """
        Test 내에서 continuous type의 KPI를 사용했을 경우 새 weight 값을 얻는 method
        :param experiment: Experiment 모델 인스턴스
        :return: list, 각 집단들의 새로운 weight 값
        """
        new_weights = [0] * len(experiment.bandit.groups) # 새 weight 받을 list 생성
        thetas_list = list(zip(*[experiment.bandit.trace['beta'+str(i)] for i in range(len(experiment.bandit.groups))]))
        # 이미 추출한 sample point들을 concatenate한 뒤 열과 행을 바꿔 알맞은 모양의 모수 리스트 생성
        for thetas in thetas_list:
            best_arm_idx = np.argmax(thetas)  # 모수 값이 가장 큰 집단의 인덱스 추출
            new_weights[best_arm_idx] += 1  # 해당 집단의 weight 값에 1 추가
        if experiment.auto_termination: # auto termination을 사용할 경우
            best_arm_idx = np.argmax(new_weights) # 최선의 집단의 인덱스 추출
            self.check_auto_termination(experiment, thetas_list, best_arm_idx) # 실험 종료 여부 확인
        return new_weights

    def check_auto_termination(self, experiment, thetas_list, best_arm_idx):
        """
        테스트 내에서 auto termination을 사용할 경우에 실험 종료 여부를 확인하는 method
        :param experiment: Experiment 인스턴스
        :param thetas_list: 모수 값 theta들이 담긴 리스트. shape=(집단 개수, 관측 횟수)여야 함.
        :param best_arm_idx: 시뮬레이션 전체를 통틀어 최선의 집단의 인덱스
        :return: 없음
        """
        regret_list = [] # regret 값들이 담길 리스트
        for thetas in thetas_list: # 각 관측의 theta들에 대해
            regret = (np.max(thetas) - thetas[best_arm_idx]) / thetas[best_arm_idx]
            # 그 관측에서 최선의 선택과 시뮬레이션 전체에서 최선의 선택의 보상의 차에 대한
            # 시뮬레이션 전체에서 최선의 선택의 보상의 비로 regret 값을 계산
            regret_list.append(regret) # 리스트에 추가
        regret_list.sort() # 작은 순으로 정렬
        pvr = regret_list[-50] # 1000개 값 중 뒤에서 50번째, 즉 upper 95 percentile 값을 potential value remaining 값으로 지정
        threshold = 0.01 # 기준값 지정
        if pvr < threshold: # PVR 값이 기준값보다 작을 경우
            experiment.end_time = timezone.now() # 실험 종료시간을 현재로 지정
            experiment.save() # 업데이트된 값을 저장함으로써 실험 종료

    def update_weights_in_test(self, experiment):
        """
        테스트 내에서 각 집단의 weight를 업데이트하는 method
        :param experiment: Experiment 인스턴스
        :return: 없음
        """
        try:
            if experiment.bandit.type == 'binary': # binary type의 KPI일 경우
                self.update_beta_dist_parameters_in_test(experiment) # 베타 분포의 모수 업데이트
                new_weights = self.get_new_weights_with_binary_reward_in_test(experiment) # 새 weight 값 얻기
            else: # continuous type의 KPI일 경우
                self.update_model_in_test(experiment) # 베이지언 모델 업데이트
                new_weights = self.get_new_weights_with_continuous_reward_in_test(experiment) # 새 weight 값 얻기
            for group, weight in zip(experiment.bandit.groups, new_weights): # 각 집단과 weight 값에 대해
                if weight == 0: # weight 값이 0일 경우
                    group.weight = 1 # 1로 보정
                else: # 그 외에
                    group.weight = weight # 각 집단의 weight 값을 새로 구한 값으로 업데이트
                group.save() # 업데이트된 값 저장
        except ValueError or FloatingPointError:
            pass

    # binary type의 KPI를 사용했을 경우 Bandit algorithm이 제대로 작동하는가.
    def test_binary_bandit_algorithm_works(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit') # Bandit algorithm 사용하는 실험 생성
        Group.objects.create_test_groups(5) # 집단 5개 생성
        Goal.objects.create_test_goals() # 목표 생성
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

    # binary type의 KPI를 사용한 여러 개의 실험이 돌아갈 때 bandit algorithm이 제대로 작동하는가. 코드 구조는 위와 대부분 같음.
    def test_binary_bandit_algorithm_works_with_multiple_experiments(self):
        Experiment.objects.create_test_experiments(3, algorithm='bandit')
        Group.objects.create_test_groups(5)
        Goal.objects.create_test_goals()
        experiments = Experiment.objects.all()
        self.create_bandits_in_test(experiments)
        winners = ['1', '3', '4'] # 각 실험별로 상정하는 최선의 집단
        for i in range(5):
            for experiment, winner in zip(experiments, winners):
                self.request_view_and_click_for_bandit_in_test(1000, experiment, winner, {'winner': 0.05, 'loser': 0.02})
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

    def test_continuous_bandit_algorithm_works(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit')  # Bandit algorithm 사용하는 실험 생성
        Group.objects.create_test_groups(5)  # 집단 5개 생성
        Goal.objects.create_test_goals(KPI='time')  # 목표 생성
        experiment = Experiment.objects.get()  # Experiment 인스턴스 지정
        self.create_bandits_in_test([experiment])  # bandit 생성
        for i in range(5):  # 총 5번 weight를 업데이트함
            self.request_view_and_leave_for_bandit_in_test(1000, experiment, '2', {'winner': 0.05, 'loser': 0.02})
            # 최선의 집단을 '2'로 상정
            # 최선의 집단에서는 0.3의 확률로, 그 외 집단에서는 0.2의 확률로 클릭이 일어나도록 하여 1000명의 request를 보냄
            self.update_weights_in_test(experiment)  # weight 업데이트
        group_assign_counts = [0] * 5  # 각 집단에 유저가 얼마나 할당되었는지 저장할 list 생성
        for i in range(1000):  # 다시 1000명의 유저에 대해
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')  # request
            assigned_group = response.data['groups'][experiment.name]  # 할당된 집단 정보 추출
            group_assign_counts[int(assigned_group)] += 1  # 해당 집단의 count 값 1 추가
        best_arm_idx = np.argmax(group_assign_counts)  # 가장 유저가 많이 할당된 집단 추출
        self.assertEqual(best_arm_idx, 2)  # 그 집단은 2가 되어야 함

    def test_continuous_bandit_algorithm_works_with_multiple_experiments(self):
        Experiment.objects.create_test_experiments(3, algorithm='bandit')
        Group.objects.create_test_groups(5)
        Goal.objects.create_test_goals(KPI='time')
        experiments = Experiment.objects.all()
        self.create_bandits_in_test(experiments)
        winners = ['1', '3', '4'] # 각 실험별로 상정하는 최선의 집단
        for i in range(5):
            for experiment, winner in zip(experiments, winners):
                self.request_view_and_leave_for_bandit_in_test(1000, experiment, winner, {'winner': 0.05, 'loser': 0.02})
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

    def test_bandit_algorithm_works_with_both_reward_types(self):
        Experiment.objects.create_test_experiments(2, algorithm='bandit')
        Group.objects.create_test_groups(5)
        experiments = Experiment.objects.all()
        goal_clicks = Goal(name='goal_clicks', KPI='clicks', act_subject='goal_clicks',experiment=experiments[0])
        goal_time = Goal(name='goal_time', KPI='time', act_subject='goal_time',experiment=experiments[1])
        goal_clicks.save()
        goal_time.save()
        self.create_bandits_in_test(experiments)
        winners = ['0', '2']
        for i in range(5):
            self.request_view_and_click_for_bandit_in_test(1000, experiments[0], winners[0], {'winner': 0.3, 'loser': 0.2})
            self.update_weights_in_test(experiments[0])
            self.request_view_and_leave_for_bandit_in_test(1000, experiments[1], winners[1],
                                                           {'winner': 0.05, 'loser': 0.02})
            self.update_weights_in_test(experiments[1])
        group_assign_counts_list = np.array([[0]*5]*2)
        for i in range(1000):
            response = self.client.post('/useractions/', {'ip': str(i)}, format='json')
            for j, experiment in enumerate(experiments):
                assigned_group = response.data['groups'][experiment.name]
                group_assign_counts_list[j][int(assigned_group)] += 1
        best_arm_idx_list = []
        for group_assign_counts in group_assign_counts_list:
            best_arm_idx_list.append(np.argmax(group_assign_counts))
        self.assertEqual(best_arm_idx_list, [0, 2])

    # binary KPI를 사용하는 경우 auto termination이 제대로 작동하는가
    def test_auto_termination_works_with_binary_reward(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit', auto_termination=True)
        Group.objects.create_test_groups(5)
        Goal.objects.create_test_goals(KPI='clicks') # CTR을 사용
        experiment = Experiment.objects.get()
        self.create_bandits_in_test([experiment])
        for i in range(5): # 총 5번 weight를 업데이트함
            self.request_view_and_click_for_bandit_in_test(1000, experiment, '2', {'winner': 0.3, 'loser': 0.2})
            self.update_weights_in_test(experiment) # weight 업데이트
            if 'Finished' in experiment.status(): # 만약 실험이 끝났을 경우
                break # 더 이상 weight를 업데이트하지 않아도 됨
        self.assertIn('Finished', experiment.status())

    # continuous KPI를 사용하는 경우 auto termination이 제대로 작동하는가
    def test_auto_termination_works_with_continuous_reward(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit', auto_termination=True)
        Group.objects.create_test_groups(5)
        Goal.objects.create_test_goals(KPI='time') # 체류시간 사용
        experiment = Experiment.objects.get()
        self.create_bandits_in_test([experiment])
        for i in range(5): # 총 5번 weight를 업데이트함
            self.request_view_and_leave_for_bandit_in_test(1000, experiment, '2', {'winner': 0.05, 'loser': 0.02})
            self.update_weights_in_test(experiment) # weight 업데이트
            if 'Finished' in experiment.status(): # 만약 실험이 끝났을 경우
                break # 더 이상 weight를 업데이트하지 않아도 됨
        self.assertIn('Finished', experiment.status())

    # end comment-out here

    # get_new_successes_and_failure 메소드가 정확하게 성공과 실패 횟수를 계산하는가. 단 CTR 계산에 한정.
    def test_method_get_new_successes_and_failures_works_precisely(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit')
        Group.objects.create_test_groups(1)
        Goal.objects.create_test_goals(KPI='clicks') # CTR을 사용
        experiment = Experiment.objects.get()
        self.create_bandits_in_test([experiment])
        group = Group.objects.get()
        view_action = experiment.name + '_view'
        click_action = experiment.goal_set.get().act_subject + '_click'
        for i in range(3):
            self.client.post('/useractions/', {'ip': str(i), 'action': view_action}, format='json') # 3번의 view
        self.client.post('/useractions/', {'ip': str(i), 'action': click_action}, format='json') # 1번의 클릭
        successes_and_failures = self.get_new_successes_and_failures_in_test(experiment, group) # 성공과 실패 횟수 계산
        self.assertEqual(successes_and_failures, (1, 2)) # 그 값은 성공 1, 실패 2가 되어야 함

    # get_new_rewards 메소드가 정확하게 보상을 계산하는가. 단 체류시간 계산에 한정.
    def test_method_get_new_rewards_works_precisely(self):
        Experiment.objects.create_test_experiments(1, algorithm='bandit')
        Group.objects.create_test_groups(1)
        Goal.objects.create_test_goals(KPI='time') # 체류시간 사용
        experiment = Experiment.objects.get()
        self.create_bandits_in_test([experiment])
        group = Group.objects.get()
        view_action = experiment.name + '_view'
        leave_action = experiment.goal_set.get().act_subject + '_leave'
        self.client.post('/useractions/', {'ip': '0', 'action': view_action}, format='json')
        time.sleep(0.05) # view의 0.05초 후에 leave를 보냄
        self.client.post('/useractions/', {'ip': '0', 'action': leave_action}, format='json')
        time.sleep(0.2) # 이전 leave의 0.2초 후에 leave를 보냄
        self.client.post('/useractions/', {'ip': '0', 'action': leave_action}, format='json')
        rewards = self.get_new_rewards_in_test(experiment, group) # 보상 계산
        self.assertEqual(len(rewards), 2) # 보상의 관측 횟수는 2여야 함
        self.assertLessEqual(rewards[0], rewards[1])
        # 보상은 정확히는 [0.05, 0.1]이어야 하나 코드 수행에 따른 오차가 있을 수 있으므로 크기비교로 검증


