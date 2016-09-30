from django import forms


PET_CHOICE = [
    ('0', 'Fire'),
    ('1', 'Water'),
    ('2', 'Plant')
]

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)


class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.PasswordInput()


class PetChooseForm(forms.Form):
    pet_name = forms.CharField(max_length=50)
    pet_kind = forms.ChoiceField(choices=PET_CHOICE)
