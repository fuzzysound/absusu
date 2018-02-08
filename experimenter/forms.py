### html form을 정의하는 파일
from django import forms
from .models import Experiment, Group

class TextWithHoursWidget(forms.TextInput):
    """
    Textbox 오른편에 시간 단위(hours)를 붙인 widget
    """
    template_name = 'widgets/text_with_hours.html'

class TextWithPercentWidget(forms.TextInput):
    """
    Textbox 오른편에 퍼센트 단위(%)를 붙인 widget
    """
    template_name = 'widgets/text_with_percent.html'

class ExperimentAdminForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = '__all__'
        widgets = {
            'assignment_update_interval': TextWithHoursWidget,
        }

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = { # 단추 형식을 바꿈
            'control': forms.CheckboxInput, # 체크박스
            'ramp_up': forms.RadioSelect, # 라디오 버튼
            'ramp_up_percent': TextWithPercentWidget,
        }

