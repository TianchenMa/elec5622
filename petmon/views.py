from django.contrib.auth import authenticate, login, logout
from django.db.models import F
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin

from petmon.forms import LoginForm, PetChooseForm
from petmon.models import User, Pet, Commodity, Repo


# Create your views here.
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

        if slug == 'choose':
            context = super(PetView, self).get_context_data()
            return render(self.request, 'petmon/choose.html', context)

        elif slug.isdecimal():
            context = super(PetView, self).get_context_data()
            user = User.objects.get(id=slug)
            context['petlist'] = user.pet_set.all()
            context['owner'] = user

            return render(self.request, 'petmon/pet_info.html', context)

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


class StoreView(BaseMixin, ListView):
    model = Commodity
    template_name = 'petmon/store.html'

    def get_context_data(self, **kwargs):
        context = super(StoreView, self).get_context_data(**kwargs)

        return context


class BuyView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == '':
            return
        else:
            raise Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'buy':
            return self.buy()
        else:
            raise Http404

    def buy(self):
        cart = {}
        context = super(BuyView, self).get_context_data()
        for i in range(1, Commodity.objects.count() + 1):
            try:
                count = int(self.request.POST[str(i)])
            except ValueError:
                pass
            else:
                if count > 0:
                    cart[str(i)] = count

        for key in cart.keys():
            comm = Commodity.objects.get(id=int(key))
            owner = context['log_user']
            count = int(cart[key])
            if Repo.objects.filter(Q(owner=owner) & Q(commodity=comm)).exists():
                boughtitem = Repo.objects.get(Q(owner=owner) & Q(commodity=comm))
                boughtitem.count = F('count') + count
            else:
                boughtitem = Repo.objects.create(commodity=comm,
                                                 count=count,
                                                 owner=owner)

            try:
                boughtitem.save()
            except Exception:
                return render(reverse('petmon:store'))

        context['object_list'] = Repo.objects.filter(owner=context['log_user'])

        return render(self.request, 'petmon/my_repo.html', context)


class RepoView(BaseMixin, ListView):
    model = Repo
    template_name = 'petmon/my_repo.html'

    def get_context_data(self, **kwargs):
        context = super(RepoView, self).get_context_data(**kwargs)
        context['object_list'] = Repo.objects.filter(owner=context['log_user'])

        return context
