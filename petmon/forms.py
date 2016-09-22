from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.PasswordInput()

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.PasswordInput()
