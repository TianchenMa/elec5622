from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin

from petmon.forms import LoginForm, PetChooseForm
from petmon.models import User, Pet


# Create your views here.
ITEM_KIND = {
    '0': {

    },
    '1': {

    },
    '2': {

    }
}


class BaseMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)
        if self.request.user.is_active:
            user = User.objects.get(pk=self.request.user.id)
        else:
            user = None

        context['log_user'] = user

        return context


class IndexView(BaseMixin, TemplateView):
    template_name = 'petmon/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        return context


class UserControlView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'signup':
            return render(self.request, 'petmon/signup.html')
        else:
            return HttpResponseRedirect(reverse('petmon:index'))

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'login':
            return self.login()
        elif slug == 'logout':
            return self.logout()
        elif slug == 'signup':
            return self.signup()
        else:
            return HttpResponseRedirect(reverse('petmon:index'))

    def login(self):
        form = LoginForm(self.request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                self.request.session.set_expiry(0)
                login(self.request, user)

        return HttpResponseRedirect(reverse('petmon:index'))

    def logout(self):
        logout(self.request)

        return HttpResponseRedirect(reverse('petmon:index'))

    def signup(self):
        user_name = self.request.POST['username']
        firstname = self.request.POST['firstname']
        lastname = self.request.POST['lastname']
        pwd = self.request.POST['password']
        e_mail = self.request.POST['email']
        user = User.objects.create(username=user_name, first_name=firstname, last_name=lastname, email=e_mail)
        user.set_password(pwd)
        try:
            user.save()
            user = authenticate(username=user_name, password=pwd)
            login(self.request, user)
        except Exception:
            pass

        return render(self.request, 'petmon/choose.html')


class PetView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'info':
            context = super(PetView, self).get_context_data()
            user = context['log_user']
            pet = user.pet_set.all()
            context['petlist'] = pet

            return render(self.request, 'petmon/pet_info.html', context)

        elif slug == 'choose':
            context = super(PetView, self).get_context_data()
            return render(self.request, 'petmon/choose.html', context)
        else:
            return

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'choose':
            return self.choose()

        else:
            return

    def choose(self):
        form = PetChooseForm(self.request.POST)
        if form.is_valid():
            context = super(PetView, self).get_context_data()
            log_user = context['log_user']
            pet_name = form.cleaned_data['pet_name']
            pet_kind = form.cleaned_data['pet_kind']
            pet = Pet(name=pet_name, kind=pet_kind, owner=log_user)
            pet.assign_attribute()
            pet.save()
        else:
            return render(self.request, 'petmon/choose.html')

        context = super(PetView, self).get_context_data()
        user = context['log_user']
        context['petlist'] = user.pet_set.all()

        return render(self.request, 'petmon/pet_info.html', context)

    def feed(self):
        return


class StoreView(BaseMixin, View):
    def get(self):
        return render(self.request, 'petmon/store.html')

    def post(self):
        return

    def get_context_data(self, **kwargs):
        context = super(StoreView, self).get_context_data()


    def buy(self):
        return
