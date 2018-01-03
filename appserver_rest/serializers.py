from rest_framework import serializers
from .models import UserAction, UserAssignment
from experimenter.randomizer import get_user_groups

class UserActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAction
        fields = '__all__'

    # 사용자 group 지정
    def create(self, validated_data):
        validated_data['groups'] = get_user_groups(validated_data['ip'])
        return super().create(validated_data)

class UserAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAssignment
        fields = '__all__'