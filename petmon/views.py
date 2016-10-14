from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
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
        context['users'] = User.objects.all()

        return context


class UserControlView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'signup':
            return render(self.request, 'petmon/signup.html')
        elif slug.isdecimal():
            context = super(UserControlView, self).get_context_data()
            if User.objects.filter(pk=slug).exists():
                user = User.objects.get(pk=slug)
            else:
                raise Http404
            context['pet'] = user.pet
            context['owner'] = user

            return render(self.request, 'petmon/pet_info.html', context)
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
                context = dict()
                context['log_user'] = user

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


class MyPetView(BaseMixin, TemplateView):

    template_name = 'petmon/pet_info.html'

    def get_context_data(self, **kwargs):
        context = super(MyPetView, self).get_context_data()
        user = context['log_user']
        context['owner'] = user
        context['pet'] = user.pet
        context['object_list'] = Repo.objects.filter(owner=context['log_user'])
        try:
            context['feed'] = self.request.session['feed']
        except KeyError:
            pass

        return context


class PetView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'choose':
            context = super(PetView, self).get_context_data()
            return render(self.request, 'petmon/choose.html', context)

        elif slug.isdecimal():
            return self.addfeed()

        else:
            raise Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'choose':
            return self.choose()

        elif slug == 'feed':
            return self.feed()

        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(PetView, self).get_context_data()
        context['object_list'] = Repo.objects.filter(owner=context['log_user'])
        context['owner'] = context['log_user']

        return context

    def addfeed(self):
        slug = self.kwargs.get('slug')
        context = self.get_context_data()
        user = context['log_user']

        try:
            item = Repo.objects.get(pk=int(slug), owner=user)
        except ObjectDoesNotExist:
            raise Http404
        else:
            pass

        try:
            self.request.session['feed'][slug] += 1
            self.request.session['feed_item'][item.commodity.name] += 1
        except KeyError as e:
            if e.args[0] == 'feed':
                self.request.session['feed_item'] = dict()
                self.request.session['feed'] = dict()
                self.request.session['feed_item'][item.commodity.name] = 1
                self.request.session['feed'][slug] = 1
            else:
                self.request.session['feed_item'][item.commodity.name] = 1
                self.request.session['feed'][slug] = 1
        else:
            pass

        self.request.session.modified = True
        context['pet'] = user.pet
        context['feed'] = self.request.session['feed_item']

        return render(self.request, 'petmon/pet_info.html', context)

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

        context = self.get_context_data()
        user = context['log_user']
        context['pet'] = user.pet

        return render(self.request, 'petmon/pet_info.html', context)

    def feed(self):
        context = self.get_context_data()
        feeds = self.request.session['feed']
        fails = dict()
        satiation, lush = 0, 0
        user = context['log_user']
        pet = Pet.objects.get(owner=user)

        for k, v in feeds.items():
            item = Repo.objects.get(pk=k)
            if item.count >= v:
                satiation += v * item.commodity.satiation
                lush += v * item.commodity.lush
                pet.satiation += satiation
                pet.lush += lush
                item.count = F('count') - v

                if item.count == 0:
                    item.delete()
                else:
                    item.save()
            else:
                fails[k] = v

        pet.save()
        context['pet'] = pet
        del self.request.session['feed']
        del self.request.session['feed_item']
        self.request.session.modified = True

        return render(self.request, 'petmon/pet_info.html', context)


class StoreView(BaseMixin, ListView):
    model = Commodity
    template_name = 'petmon/store.html'

    def get_context_data(self, **kwargs):
        context = super(StoreView, self).get_context_data(**kwargs)

        return context


class BuyView(BaseMixin, View):
    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if not self.request.user.is_active:
            raise Http404

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
                return render(reverse('petmon:store'), context)

        context['object_list'] = Repo.objects.filter(owner=context['log_user'])

        return render(self.request, 'petmon/my_repo.html', context)


class RepoView(BaseMixin, ListView):
    model = Repo
    template_name = 'petmon/my_repo.html'

    def get_context_data(self, **kwargs):
        context = super(RepoView, self).get_context_data(**kwargs)
        context['object_list'] = Repo.objects.filter(owner=context['log_user'])

        return context
