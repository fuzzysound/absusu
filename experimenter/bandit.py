""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/experimenter/bandit.py
"""
"""
Bandit algorithm 이 동작하도록 하는 모듈
"""
from django.utils import timezone
from appserver_rest.models import UserAction
from threading import Timer
from scipy.stats import beta, gaussian_kde
import numpy as np
import pymc3 as pm
from pymc3.distributions import Interpolated

BINARY_REWARD = ('clicks',) # 결과가 0과 1로 구분되는 KPI들
CONTINUOUS_REWARD = ('time',) # 결과가 실수 집합의 원소인 KPI들

def from_posterior(param, samples):
    """
    이전 update의 posterior를 새 update의 prior로 사용하기 위한 함수
    :param param: 파라미터 이름
    :param samples: 이전 update의 posterior에서 추출된 sample points
    :return: Interpolated object, sample points로부터 보간된 분포
    """
    smin, smax = np.min(samples), np.max(samples) # sample points들의 최소값과 최대값 추출
    width = smax - smin
    x = np.linspace(smin, smax, 100) # 최소값과 최대값 사이 100개 points 생성
    y = gaussian_kde(samples)(x) # kernel density estimation을 통해 적당한 pdf를 생성하여 y값 생성
    x = np.concatenate([[x[0] - 3 * width], x, [x[-1] + 3 * width]])
    y = np.concatenate([[0], y, [0]]) # sample points에 포함되지 않은 값들에도 아주 적은 확률을 할당해주기 위함
    return Interpolated(param, x, y)

def from_posterior_halfnormal(param, samples):
    """
    half-normal 분포의 prior를 업데이트하기 위한 함수. from_posterior와 거의 유사한 방법을 씀.
    """
    smax = np.max(samples)
    width = smax
    x = np.linspace(0, smax, 100) # half-normal 분포는 X 값이 0 이상에서만 존재하므로
    y = 2 * gaussian_kde(samples)(x) # y 값이 가우시안 분포의 2배이므로
    x = np.concatenate([x, [x[-1] + 6*width]])
    y = np.concatenate([y, [0]])
    return Interpolated(param, x, y)



class Bandit:

    def __init__(self, experiment):
        self.experiment = experiment  # 해당 실험
        self.groups = experiment.group_set.all()  # 실험의 집단들
        self.goal = experiment.goal_set.get()  # 실험의 목표
        self.last_update_time = experiment.start_time  # 최근 업데이트 시간
        self.next_update_time = experiment.start_time + timezone.timedelta(hours=experiment.assignment_update_interval)
        # 다음 업데이트 시간 (= 최근 업데이트 시간 + assignment update interval)
        if self.goal.KPI in BINARY_REWARD: # KPI가 binary이면
            self.type = 'binary' # 타입 지정
            self.parameters = [(1, 1)] * len(self.groups)  # 각 집단별 베타 분포의 모수 값. 시작은 (1, 1).
        else: # KPI가 continuous이면
            self.type = 'continuous' # 타입 지정
            self.model = pm.Model() # 베이지언 모델 생성
            with self.model:
                alpha = pm.Normal('alpha', mu=0, sd=10) # intercept
                beta = [] # coefficients
                for i in range(len(self.groups)):
                    beta.append(pm.Normal('beta' + str(i), mu=0, sd=10)) # 집단 수만큼 coefficient 추가
                sigma = pm.HalfNormal('sigma', sd=1)
                mu = alpha # 초기 weight 값은 집단마다 골고루 주기 위해 intercept만을 모델에 포함시킴
                Y_obs = pm.Normal('Y_obs', mu=mu, sd=sigma, observed=[]) # 모델 구조 정의
                self.trace = pm.sample(1000, cores=1) # 이 모델로부터 추출된 sample points
                # theano 사용시 deadlock 이슈가 있어 멀티코어를 사용하지 않음
        for group in experiment.group_set.all():
            group.weight = 1  # 모든 집단의 weight 초기값을 1로 설정

    def get_new_successes_and_failures(self, group):
        """
        이전 업데이트 이후 새로 기록된 성공과 실패 횟수를 반환하는 method
        :param group: Group 인스턴스
        :return: tuple, (성공 횟수, 실패 횟수)
        """
        if self.goal.KPI == 'clicks': # KPI가 CTR일 경우의 계산
            view_action = self.experiment.name + '_view'  # view에 대해 action 값으로 받은 문자열 지정
            click_action = self.goal.act_subject + '_click'  # click에 대해 action 값으로 받은 문자열 지정
            impressions = UserAction.objects.query_action(self.experiment, group, view_action,
                                                          self.last_update_time).count()
            clicks = UserAction.objects.query_action(self.experiment, group, click_action,
                                                     self.last_update_time).count()
            # 최근 업데이트 이후 생성된 로그 중 이 실험과 집단에서 view와 click을 action 값으로 포함한 로그의 수를 각각 센다
            if clicks > impressions:  # click이 view보다 자주 일어났을 경우 (있어서는 안 될 경우)
                impressions = clicks  # impressions 값 보정
            return clicks, impressions - clicks
        else: # 등록되지 않은 KPI일 경우
            raise ValueError("Unknown KPI:", self.goal.KPI)

    def get_new_rewards(self, group):
        """
        이전 업데이트 이후 새로 기록된 보상(reward)을 반환하는 method
        :param group: Group 인스턴스
        :return: list, 모든 보상
        """
        if self.goal.KPI == 'time': # KPI가 체류시간일 경우의 계산
            view_action = self.experiment.name + '_view' # view에 대해 action 값으로 받은 문자열 지정
            leave_action = self.goal.act_subject + '_leave' # leave에 대해 action 값으로 받은 문자열 지정
            time_on_page_list = [] # 체류시간이 들어갈 list
            earliest_latest_leave_time = self.last_update_time
            # earliest_latest_leave_time 변수는 last_update_time을 업데이트하는 데 이용됨.
            # 모든 이용자의 마지막 leave 중 가장 이른 것을 last_update_time으로 업데이트해야 하기 때문.
            # 로그가 없을 경우 last_update_time 값을 변경하지 않기 위해 이 변수의 초기값을 last_update_time으로 줌
            leaves = UserAction.objects.query_action(self.experiment, group, leave_action, self.last_update_time)
            # leave_action이 포함된 모든 로그를 가져옴
            distinct_ip_list = leaves.values_list('ip') # 고유한 ip 주소 추출
            for ip in distinct_ip_list: # 각각의 ip 주소에 대해
                # 비교는 다음과 같이 이루어진다.
                # 한 ip가 여러 leave를 남겼다면 각각의 leave에 대해 체류시간을 구하며
                # 로그가 아래와 같은 순서로 찍혔으면
                # view0 - last_leave - view1 - view2 - view3 - leave (last_leave는 그 이전의 leave를 의미)
                # 체류시간은 leave의 시간과 view3의 시간의 차로 구해진다
                # 만약 leave 이전에 view가 없었다면
                # 체류시간은 leave의 시간과 last_leave의 시간의 차의 1/2로 구해진다.
                leaves_of_the_ip = leaves.filter(ip__exact=ip[0]).order_by('time') # 이 ip가 남긴 leave를 시간순 정렬
                last_leave_time = self.last_update_time
                # 가장 처음의 leave는 이전 leave가 없으므로, 이 때의 초기값을 last_update_time으로 줌
                for leave in leaves_of_the_ip: # 이 ip 주소의 모든 leave에 대해
                    views = UserAction.objects.filter(ip__exact=ip[0]).query_action(self.experiment, group,
                                                                                    view_action,
                                                                                    last_leave_time,
                                                                                    leave.time).order_by('-time')
                    # leave와 그 이전 leave 사이의 모든 view를 최신순으로 정렬
                    if views: # view가 존재할 경우
                        latest_view_time = views[0].time # 그 중 가장 최신의 view를 추출
                        time_on_page = leave.time - latest_view_time # 체류시간 계산
                        time_on_page_list.append(time_on_page.total_seconds()) # 초 단위로 환산해 리스트에 추가
                    else: # view가 없을 경우
                        time_on_page = (leave.time - last_leave_time) / 2 # 임의로 체류시간 계산
                        time_on_page_list.append(time_on_page.total_seconds()) # 리스트에 추가
                    last_leave_time = leave.time
                    # last_leave_time 값은 계속 덮어씌워져 결국에는 가장 나중의 leave의 시간 값이 됨
                if last_leave_time < earliest_latest_leave_time:
                    earliest_latest_leave_time = last_leave_time # 모든 이용자의 마지막 leave 중 가장 이른 것으로 지정
            return earliest_latest_leave_time, time_on_page_list
        else: # 등록되지 않은 KPI일 경우
            raise ValueError("Unknown KPI:", self.goal.KPI)

    # 베타 분포의 모수를 업데이트하는 method
    def update_beta_dist_parameters(self):
        for i, group in enumerate(self.groups):  # 모든 집단에 대해
            successes, failures = self.get_new_successes_and_failures(group) # 새로운 성공과 실패 횟수 얻기
            self.parameters[i] = tuple(map(sum, zip(self.parameters[i], (successes, failures))))  # 업데이트
        self.last_update_time = timezone.now()  # 최근 업데이트 시간 갱신
        self.next_update_time += timezone.timedelta(
            hours=self.experiment.assignment_update_interval)  # 다음 업데이트 시간 갱신

    # 베이지언 모델을 업데이트하는 method
    def update_model(self):
        rewards = [] # 관측값(보상)이 담길 리스트
        dummy_coded_group_variables = [] # 더미코딩된 변수 값이 담길 리스트
        # 예를 들어 집단이 5개이면 변수의 개수는 5개이고
        # 한 sample point가 유저가 첫 번째 집단에 배정됐을 때 나온 것이라면 이 때 X = [1, 0, 0, 0, 0]
        best_earliest_latest_leave_time = None
        for i, group in enumerate(self.groups): # 모든 집단에 대해
            earlies_latest_leave_time, rewards_of_the_group = self.get_new_rewards(group) # 새로운 보상 리스트 얻기
            dummy = [0] * len(self.groups)
            dummy[i] += 1 # 이 집단에 대한 더미코딩된 변수 값 생성
            dummy_coded_group_variable = [dummy] * len(rewards_of_the_group) # 이 값을 보상 개수만큼 만듬
            rewards += rewards_of_the_group # 리스트에 추가
            dummy_coded_group_variables += dummy_coded_group_variable # 리스트에 추가
            if best_earliest_latest_leave_time is None or earlies_latest_leave_time < best_earliest_leave_time:
                best_earliest_leave_time = earlies_latest_leave_time
        self.last_update_time = best_earliest_latest_leave_time # 그 값으로 last_update_time을 업데이트
        self.next_update_time += timezone.timedelta(
            hours=self.experiment.assignment_update_interval)  # 다음 업데이트 시간 갱신
        dummy_coded_group_variables = list(zip(*dummy_coded_group_variables))
        # 열과 행을 바꾸어주어 아래에서 모델에 추가할 수 있도록 함.
        # shape가 (집단 개수, 보상 개수)에서 (보상 개수, 집단 개수)로 바뀜
        self.model = pm.Model() # 베이지언 모델을 새로 생성해 모델을 새로 정의할 수 있도록 함
        with self.model:
            alpha = from_posterior('alpha', self.trace['alpha']) # intercept 업데이트
            beta = []
            for i in range(len(self.groups)):
                beta.append(from_posterior('beta' + str(i), self.trace['beta' + str(i)])) # 각각의 coefficient 업데이트
            sigma = from_posterior_halfnormal('sigma', self.trace['sigma']) # error 업데이트
            mu = alpha
            if rewards:
                for i in range(len(beta)):
                    mu += beta[i] * dummy_coded_group_variables[i]
            # for loop을 이용해 mu 안에 각 coefficient와 변수를 곱한 것을 집어넣음. np.dot은 여기서 사용할 수 없음.
            Y_obs = pm.Normal('Y_obs', mu=mu, sd=sigma, observed=rewards) # 모델 정의
            self.trace = pm.sample(1000, cores=1) # 1000개의 샘플 추출.

    # binary type의 KPI를 사용했을 경우 새 weight 값을 얻는 method
    def get_new_weights_with_binary_reward(self):
        new_weights = [0] * len(self.groups)  # 새 weight 받을 list 생성
        thetas_list = [] # 모든 theta 값을 담을 리스트. Auto termination을 하기 위함.
        for i in range(1000):  # 1000번 실험하는 Monte-Carlo test
            thetas = [beta.rvs(a, b) for a, b in self.parameters]  # 베타 분포로 각 집단의 이항 분포 모수 theta 생성
            thetas_list.append(thetas) # 리스트에 추가
            best_arm_idx = np.argmax(thetas)  # 모수 값이 가장 큰 집단의 인덱스 추출
            new_weights[best_arm_idx] += 1  # 해당 집단의 weight 값에 1 추가
        if self.experiment.auto_termination: # auto termination을 사용할 경우
            best_arm_idx = np.argmax(new_weights) # 최선의 집단의 인덱스 추출
            self.check_auto_termination(thetas_list, best_arm_idx) # 실험 종료 여부 확인
        return new_weights

    # continuous type의 KPI를 사용했을 경우 새 weight 값을 얻는 method
    def get_new_weights_with_continuous_reward(self):
        new_weights = [0] * len(self.groups) # 새 weight 받을 list 생성
        thetas_list = list(zip(*[self.trace['beta' + str(i)] for i in range(len(self.groups))]))
        # 이미 추출한 sample point들을 concatenate한 뒤 열과 행을 바꿔 알맞은 모양의 모수 리스트 생성
        for thetas in thetas_list:
            best_arm_idx = np.argmax(thetas)  # 모수 값이 가장 큰 집단의 인덱스 추출
            new_weights[best_arm_idx] += 1  # 해당 집단의 weight 값에 1 추가
        if self.experiment.auto_termination: # auto termination을 사용할 경우
            best_arm_idx = np.argmax(new_weights) # 최선의 집단의 인덱스 추출
            self.check_auto_termination(thetas_list, best_arm_idx) # 실험 종료 여부 확인
        return new_weights

    def check_auto_termination(self, thetas_list, best_arm_idx):
        """
        auto termination을 사용할 경우에 실험 종료 여부를 확인하는 method
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
        pvr = regret_list[-50]
        # 1000개 값 중 뒤에서 50번째, 즉 upper 95 percentile 값을 potential value remaining 값으로 지정
        threshold = 0.01 # 기준값 지정
        if pvr < threshold: # PVR 값이 기준값보다 작을 경우
            self.experiment.end_time = timezone.now() # 실험 종료시간을 현재로 지정
            self.experiment.save() # 업데이트된 값을 저장함으로써 실험 종료

    # 각 집단의 weight를 업데이트하는 method
    def update_weights(self):
        try:
            if self.type == 'binary': # binary type의 KPI일 경우
                self.update_beta_dist_parameters()  # 베타 분포의 모수 업데이트
                new_weights = self.get_new_weights_with_binary_reward() # 새 weight 값 얻기
            else: # continuous type의 KPI일 경우
                self.update_model() # 베이지언 모델 업데이트
                new_weights = self.get_new_weights_with_continuous_reward() # 새 weight 값 얻기
            for group, weight in zip(self.groups, new_weights):  # 각 집단과 weight 값에 대해
                if weight == 0:  # weight 값이 0일 경우
                    group.weight = 1  # 1로 보정
                else:  # 그 외에
                    group.weight = weight  # 각 집단의 weight 값을 새로 구한 값으로 업데이트
                group.save()  # 업데이트된 값 저장
                # 다음 업데이트 시간에 이 method를 실행하도록 하는 타이머 생성
        except ValueError or FloatingPointError:
            pass # 베이지언 모델 업데이트 시 gradient explosion이 일어날 경우 무시하기 위한 예외처리
        finally:
            if self.next_update_time < self.experiment.end_time:  # 만약 다음 업데이트 시간이 실험 종료 이전이면
                Timer((self.next_update_time - timezone.now()).total_seconds(), self.update_weights).start()
