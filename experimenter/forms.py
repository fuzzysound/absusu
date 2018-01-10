from django import forms
from .models import Group

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = {
            'control': forms.CheckboxInput,
            'ramp_up': forms.RadioSelect,
        }