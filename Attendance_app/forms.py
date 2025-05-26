from django import forms
from .models import *

class CompanyLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class EmployeeRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Employee
        fields = ['company', 'employee_id', 'name', 'email', 'password','face_image']

class CompanyRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Company
        fields = ['name', 'email', 'password', 'smtp_email', 'use_tls']