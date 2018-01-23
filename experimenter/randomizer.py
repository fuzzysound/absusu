# Randomization algorithm

from experimenter import models
from appserver_rest.models import UserAssignment
import hashlib
import numpy as np

# ip에 해당하는 group을 반환하는 함수
def get_user_groups(ip):
    """
    :param ip: 접속한 유저의 ip 주소
    :return: 유저가 할당된 그룹 정보, dict
    """
    groups = {} # 유저가 할당된 그룹 정보가 저장될 dict
    try:
        hash_indexes = UserAssignment.objects.get(ip=ip).hash_indexes # UserAssignment DB에 기록이 이미 있으면 가져온다
    except UserAssignment.DoesNotExist:
        hash_indexes = {} # 없으면 빈 dictionary로 지정
    for experiment in models.Experiment.objects.active(): # 현재 active한 실험마다 group 지정
        if hash_indexes.get(experiment.name, 0) == 0: # 만약 해당 experiment에 대해 user가 assign되어있지 않으면
            hash_indexes = assign(ip, experiment, hash_indexes) # 새로 assign해줌
        hash_index = hash_indexes[experiment.name] # 해당 experiment에서 user가 assign된 hash index
        groups[experiment.name] = groupify(hash_index, experiment) # hash index를 바탕으로 group 결정
    return groups

# 유저를 group에 hash partition에 assign하고 DB에 기록하는 함수
def assign(ip, experiment, hash_indexes):
    """
    :param ip: 접속한 유저의 ip 주소
    :param experiment: Experiment 모델의 인스턴스, 집단을 지정할 실험
    :param hash_indexes: 업데이트해야 할 hash indexes 정보
    :return: 업데이트된 hash indexes, dict
    """
    hash_id = experiment.name + ip # experiment의 이름과 ip 주소를 결합해 고유한 hash id 생성
    hash_value = hashlib.md5(hash_id.encode()).hexdigest() # md5를 이용해 hash id를 16진수의 hash value로 변환
    hash_index = int(hash_value, 16) % 1000 # hash value를 1000으로 나눈 나머지를 hash index로 지정 (0~999 사이의 값)
    hash_indexes[experiment.name] = hash_index # memory의 hash_indexes 변수를 업데이트
    UserAssignment.objects.update_or_create(ip=ip, defaults={'hash_indexes': hash_indexes}) # DB에 업데이트 혹은 새로 생성
    return hash_indexes


# 인수로 받은 hash index에 알맞는 group을 반환하는 함수
def groupify(hash_index, experiment):
    """
    :param hash_index: 집단을 지정하기 위해 필요한 hash index
    :param experiment: Experiment 모델의 인스턴스, 집단을 지정할 실험
    :return: 유저가 할당된 집단 이름, str
    """
    groups = list(experiment.group_set.all()) # 모든 group들의 list
    group_weights = []  # 해당 experiment의 group별 weight를 넣기 위한 list
    for group in groups:  # 넣는 작업
        group_weights.append(group.weight)
        if group.control:
            control_group = group # control group은 따로 지정해 둠
    group_ratios = np.array(group_weights) / sum(group_weights) # weight들을 ratio로 변환 (0~1 사이의 값)
    group_ratios_cum = np.cumsum(group_ratios) # cumulative ratio로 변환 (마지막 값은 항상 1)
    partition_separator = [0] + list(group_ratios_cum*1000) # 각각의 hash partition들이 어느 group에 들어가는지의 기준이 되는 숫자들
    for i in range(len(partition_separator)-1): # 특정 기준숫자들 사이에 hash index가 위치하면
        if partition_separator[i] <= hash_index < partition_separator[i+1]:
            left_separator = partition_separator[i] # 왼쪽 기준숫자 지정
            right_separator = partition_separator[i+1] # 오른쪽 기준숫자 지정
            assigned_group = groups[i] # 해당 group에 지정
            break
    else: # 있어서는 안 될 경우
        return ""

    if assigned_group.control or not assigned_group.ramp_up: # assign된 group이 control group이거나 ramp up을 사용하지 않는 경우
        return assigned_group.name # 그대로 assign된 group의 이름 반환
    else: # ramp up을 사용하는 경우
        rampup_separator = left_separator + (right_separator-left_separator)*assigned_group.ramp_up_percent/100 # 새로운 기준숫자
        if hash_index < rampup_separator: # hash index가 그 기준숫자보다 작으면
            return assigned_group.name # assign된 group의 이름 반환
        else: # 아닐 경우
            return control_group.name # control group의 이름 반환

# TODO: automatic ramp-up


