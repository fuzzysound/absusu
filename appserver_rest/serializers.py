from rest_framework import serializers
from .models import UserAction

class UserActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAction
        fields = ('id', 'user_id', 'group', 'time', 'action', )

