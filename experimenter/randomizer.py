# Randomization algorithm

import random
from experimenter import models
from appserver_rest.models import UserAssignment
import hashlib

# ip에 해당하는 group을 반환하는 함수
def get_user_groups(ip):
    groups = {}
    try:
        assignment = UserAssignment.objects.get(ip=ip).assignment # UserAssignment DB에 기록이 이미 있으면 가져온다
    except UserAssignment.DoesNotExist:
        assignment = {} # 없으면 빈 dictionary로 지정
    for experiment in models.Experiment.objects.active(): # 현재 active한 실험마다 group 지정
        # ramp_up = experiment.ramp_up # 실험에서 ramp up 사용하는지 여부
        ramp_up = False
        if assignment.get(experiment.name, 0) == 0: # 만약 해당 experiment에 대해 user가 assign되어있지 않으면
            assignment = assign(ip, experiment, assignment, ramp_up) # 새로 assign해줌
        groups[experiment.name] = groupify(assignment[experiment.name], ramp_up)
    return groups

# 유저를 group에 assign하고 (ramp up 사용할 경우 hash partition에 assign하고) DB에 기록하는 함수
def assign(ip, experiment, assignment, ramp_up):

    # if ramp_up:
    #     assignment = hash_assign(ip, experiment, assignment)
    #
    # else:
    #     assignment = group_assign(experiment, assignment)

    assignment = group_assign(experiment, assignment)

    UserAssignment.objects.update_or_create(ip=ip, defaults={'assignment': assignment}) # DB에 업데이트 혹은 새로 생성
    return assignment

# def hash_assign(ip, experiment, assignment):
#     hash_id = experiment.name + ip
#     hash_value = hashlib.md5(hash_id.encode()).hexdigest()
#     hash_index = int(hash_value, 16) % 1000
#     assignment[experiment.name] = hash_index
#     return assignment
#
#
def group_assign(experiment, assignment):
    group_names = []  # 해당 experiment의 모든 group 이름을 넣기 위한 list
    group_weights = []  # 해당 experiment의 group별 weight를 넣기 위한 list
    for group in experiment.group_set.all():  # 넣는 작업
        group_names.append(group.name)
        group_weights.append(group.weight)
    assigned_group = random.choices(group_names, weights=group_weights)[0]  # weight에 따라 random choice
    assignment[experiment.name] = assigned_group
    return assignment

# 만약 ramp up을 사용할 경우, 이 함수는 인수로 받은 hash partition에 알맞는 group을 return할 것임.
def groupify(experiment_assignment, ramp_up):
    if ramp_up:
        pass # Ramp up 적용할 때 채우기
    else: 
        return experiment_assignment

