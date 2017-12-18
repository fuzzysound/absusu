from rest_framework import serializers
from .models import UserAction

class UserActionSerializer(serializers.Serializer):
    class Meta:
        model = UserAction
        fields = ('id', 'group', 'time', 'action', )

        