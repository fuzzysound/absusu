import random
from experimenter import models
from appserver_rest.models import UserAssignment


def get_user_groups(ip):
    groups = {}
    try:
        assignment = UserAssignment.objects.get(ip=ip).assignment
    except UserAssignment.DoesNotExist:
        assignment = {}
    for experiment in models.Experiment.objects.active():
        ramp_up = experiment.ramp_up
        if assignment.get(experiment.name, 0) == 0:
            assignment = assign(ip, experiment, assignment, ramp_up)
        groups[experiment.name] = groupify(assignment[experiment.name], ramp_up)
    return groups

def assign(ip, experiment, assignment, ramp_up):
    if ramp_up:
        pass # Ramp up 적용할 때 채우기
    else:
        group_names = []
        group_weights = []
        for group in experiment.group_set.all():
            group_names.append(group.name)
            group_weights.append(group.weight)
        assigned_group = random.choices(group_names, weights=group_weights)[0]
        assignment[experiment.name] = assigned_group
        UserAssignment.objects.filter(ip=ip).update_or_create(assignment=assignment)
        return assignment

def groupify(experiment_assignment, ramp_up):
    if ramp_up:
        pass # Ramp up 적용할 때 채우기
    else:
        return experiment_assignment

