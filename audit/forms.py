from django import forms
from .models import AuditLog

class AuditLogSearchForm(forms.Form):
    user = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search by username...'}))
    action_type = forms.ChoiceField(required=False, choices=[('', 'All Actions')])
    target_model = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Model name...'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['action_type'].choices = [('', 'All Actions')] + list(AuditLog.ACTION_TYPES)