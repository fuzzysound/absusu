import random

user_group = {}

def get_user_group(user_id):
    user_group.setdefault(user_id, random.choice(['A', 'B']))
    return user_group[user_id]

