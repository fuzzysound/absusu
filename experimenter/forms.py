""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/experimenter/forms.py
"""
"""
html form 을 정의하는 파일
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
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

    def clean(self):
        cleaned_data = super().clean() # 기존의 clean()을 거친 데이터 받기
        experiment = cleaned_data['experiment'] # 외래키로 참조하는 Experiment 인스턴스

        # automatic ramp up을 사용할 때 ramp up 종료시간이 실험 시작시간과 종료시간 사이에 있지 않을 경우
        if self.cleaned_data['ramp_up'] == 'automatic' and not \
                (experiment.start_time < cleaned_data['ramp_up_end_time'] < experiment.end_time):
            raise ValidationError(_("Ramp up end time must be between start time and end time of the experiment!"),
                                      code='ramp_up_end_time_not_valid')
