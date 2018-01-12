### http 프로토콜 데이터를 파이썬 데이터로 변환해주는 파일
from rest_framework import serializers
from .models import UserAction, UserAssignment
from experimenter.randomizer import get_user_groups

class UserActionSerializer(serializers.ModelSerializer): # UserAction 모델의 serializer
    class Meta:
        model = UserAction
        fields = '__all__'

    # create 메소드를 override하여 매 request마다 사용자 group 지정
    def create(self, validated_data):
        """
        :param validated_data: full_clean()을 거친 JSON request data
        :return: groups 정보가 채워진 JSON response data
        """
        validated_data['groups'] = get_user_groups(validated_data['ip'])
        return super().create(validated_data)

class UserAssignmentSerializer(serializers.ModelSerializer): # UserAssignment 모델의 serializer
    class Meta:
        model = UserAssignment
        fields = '__all__'