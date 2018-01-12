### html form을 정의하는 파일
from django import forms
from .models import Group

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = { # 단추 형식을 바꿈
            'control': forms.CheckboxInput, # 체크박스
            'ramp_up': forms.RadioSelect, # 라디오 버튼
        }