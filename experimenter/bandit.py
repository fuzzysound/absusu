### Bandit algorithm이 동작하도록 하는 모듈
from django.utils import timezone
from appserver_rest.models import UserAction
from threading import Timer
from scipy.stats import beta
import numpy as np

class Bandit:
    def __init__(self, experiment):
        self.experiment = experiment # 해당 실험
        self.groups = experiment.group_set.all() # 실험의 집단들
        self.goal = experiment.goal_set.get() # 실험의 목표
        self.parameters = [(1, 1)] * len(self.groups) # 각 집단별 베타 분포의 모수 값. 시작은 (1, 1).
        self.last_update_time = experiment.start_time # 최근 업데이트 시간
        self.next_update_time = experiment.start_time + timezone.timedelta(hours=experiment.assignment_update_interval)
        # 다음 업데이트 시간 (= 최근 업데이트 시간 + assignment update interval)

        for group in experiment.group_set.all():
            group.weight = 1 # 모든 집단의 weight 초기값을 1로 설정

    # 베타 분포의 모수를 업데이트하는 method
    def update_parameters(self):
        for i, group in enumerate(self.groups): # 모든 집단에 대해
            view_action = self.experiment.name + '_view' # view에 대해 action 값으로 받은 문자열 지정
            click_action = self.goal.act_subject + '_click' # click에 대해 action 값으로 받은 문자열 지정
            impressions = UserAction.objects.query_action(self.experiment, group, view_action, self.last_update_time).count()
            clicks = UserAction.objects.query_action(self.experiment, group, click_action, self.last_update_time).count()
            # 최근 업데이트 이후 생성된 로그 중 이 실험과 집단에서 view와 click을 action 값으로 포함한 로그의 수를 각각 센다
            if clicks > impressions: # click이 view보다 자주 일어났을 경우 (있어서는 안 될 경우)
                impressions = clicks # impressions 값 보정
            self.parameters[i] = tuple(map(sum, zip(self.parameters[i], (clicks, impressions-clicks)))) # 업데이트

    # 각 집단의 weight를 업데이트하는 method
    def update_weights(self):
        self.update_parameters() # 베타 분포의 모수 업데이트
        self.last_update_time = timezone.now() # 최근 업데이트 시간 갱신
        self.next_update_time += timezone.timedelta(hours=self.experiment.assignment_update_interval) # 다음 업데이트 시간 갱신
        new_weights = np.array([0] * len(self.groups)) # 새 weight 받을 list 생성
        for i in range(10000): # 10000번 실험하는 Monte-Carlo test
            thetas = [beta.rvs(a, b) for a, b in self.parameters] # 베타 분포로 각 집단의 이항 분포 모수 생성
            best_arm_idx = np.argmax(thetas) # 모수 값이 가장 큰 집단의 인덱스 추출
            new_weights[best_arm_idx] += 1 # 해당 집단의 weight 값에 1 추가
        for group, weight in zip(self.groups, new_weights): # 각 집단과 weight 값에 대해
            if weight == 0: # weight 값이 0일 경우
                group.weight = 1 # 1로 보정
            else: # 그 외에
                group.weight = weight # 각 집단의 weight 값을 새로 구한 값으로 업데이트
            group.save() # 업데이트된 값 저장
        if self.next_update_time < self.experiment.end_time: # 만약 다음 업데이트 시간이 실험 종료 이전이면
            Timer((self.next_update_time - timezone.now()).seconds, self.update_weights).start()
            # 다음 업데이트 시간에 이 method를 실행하도록 하는 타이머 생성