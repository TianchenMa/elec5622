from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, TemplateView
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

        elif slug == 'add_feed':
            return self.add_to_feed()

        else:
            raise Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'choose':
            return self.choose_item()

        elif slug == 'feed':
            return self.feed_pet()

        elif slug == 'clean_feed':
            return self.clean_feed_basket()

        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(PetView, self).get_context_data()
        user = context['log_user']
        context['object_list'] = Repo.objects.filter(owner=user)
        context['owner'] = user
        context['pet'] = user.pet

        return context

    def add_to_feed(self):
        context = self.get_context_data()
        item_id = self.request.GET.get('id')
        user = context['log_user']

        try:
            count = int(self.request.GET.get('count'))
        except ValueError:
            try:
                context['feed'] = self.request.session['feed_item']
            except KeyError:
                pass

            context['my_item'] = Repo.objects.filter(owner=user)

            return render(self.request, 'petmon/pet_info.html', context)

        try:
            item = Repo.objects.get(pk=item_id)
        except ObjectDoesNotExist:
            raise Http404
        else:
            pass

        try:
            self.request.session['feed'][item_id] += count
            self.request.session['feed_item'][item.commodity.name] += count
        except KeyError as e:
            if e.args[0] == 'feed':
                self.request.session['feed_item'] = dict()
                self.request.session['feed'] = dict()
                self.request.session['feed_item'][item.commodity.name] = count
                self.request.session['feed'][item_id] = count
            else:
                self.request.session['feed_item'][item.commodity.name] = count
                self.request.session['feed'][item_id] = count
        else:
            pass

        self.request.session.modified = True
        context['feed'] = self.request.session['feed_item']
        context['my_item'] = Repo.objects.filter(owner=user)

        return render(self.request, 'petmon/pet_info.html', context)

    def clean_feed_basket(self):
        del self.request.session['feed']
        del self.request.session['feed_item']
        context = self.get_context_data()
        context['pet'] = context['log_user'].pet

        return render(self.request, 'petmon/pet_info.html', context)

    def choose_item(self):
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

    def feed_pet(self):
        context = self.get_context_data()
        feeds = self.request.session['feed']
        fails = dict()
        user = context['log_user']
        pet = Pet.objects.get(owner=user)

        for k, v in feeds.items():
            item = Repo.objects.get(pk=k)
            satiation, lush = 0, 0
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
        context = super(StoreView, self).get_context_data()

        try:
            context['my_item'] = Repo.objects.filter(owner=context['log_user'])
        except KeyError:
            pass

        try:
            context['cart'] = self.request.session['cart_item']
            context['amount'] = self.request.session['amount']
        except KeyError:
            pass

        return context


class BuyView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        context = super(BuyView, self).get_context_data()

        if slug == 'add_to_cart':
            if self.request.user.is_active:
                return self.add_to_cart()
            else:
                return HttpResponseRedirect(reverse('petmon:store'), context)
        else:
            raise Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if not self.request.user.is_active:
            raise Http404

        if slug == 'buy':
            return self.buy()
        elif slug == 'clean_cart':
            return self.clean_cart()
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(BuyView, self).get_context_data()
        user = context['log_user']
        context['pet'] = user.pet
        context['object_list'] = Commodity.objects.all()

        return context

    def add_to_cart(self):
        context = self.get_context_data()
        comm_id = self.request.GET.get('id')
        user = context['log_user']

        try:
            count = int(self.request.GET.get('count'))

            if count <= 0:
                raise ValueError
        except ValueError:
            try:
                context['cart'] = self.request.session['cart_item']
                context['amount'] = self.request.session['amount']
            except KeyError:
                pass

            context['my_item'] = Repo.objects.filter(owner=user)

            return render(self.request, 'petmon/store.html', context)

        try:
            comm = Commodity.objects.get(pk=int(comm_id))
        except ObjectDoesNotExist:
            raise Http404
        else:
            pass

        try:
            self.request.session['cart'][comm_id] += count
            self.request.session['cart_item'][comm.name] += count
            self.request.session['amount'] += comm.price * count
        except KeyError as e:
            if e.args[0] == 'cart':
                self.request.session['cart_item'] = dict()
                self.request.session['cart'] = dict()
                self.request.session['cart_item'][comm.name] = count
                self.request.session['cart'][comm_id] = count
                self.request.session['amount'] = 0
                self.request.session['amount'] = comm.price * count
            else:
                self.request.session['cart_item'][comm.name] = count
                self.request.session['cart'][comm_id] = count
                self.request.session['amount'] += comm.price * count
        else:
            pass

        self.request.session.modified = True
        context['cart'] = self.request.session['cart_item']
        context['my_item'] = Repo.objects.filter(owner=user)
        context['amount'] = self.request.session['amount']

        return render(self.request, 'petmon/store.html', context)

    def clean_cart(self):
        context = self.get_context_data()
        context['my_item'] = Repo.objects.filter(owner=context['log_user'])
        del self.request.session['cart']
        del self.request.session['cart_item']
        del self.request.session['amount']

        return HttpResponseRedirect(reverse('petmon:store'), context)

    def buy(self):
        cart = self.request.session['cart']
        context = self.get_context_data()
        owner = context['log_user']
        amount = int(self.request.session['amount'])

        if amount > owner.step:
            context['my_item'] = Repo.objects.filter(owner=owner)
            context['amount'] = amount

            return HttpResponseRedirect(reverse('petmon:store'), context)
        else:
            owner.step -= amount
            owner.save()

        for key in cart.keys():
            comm = Commodity.objects.get(id=int(key))
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
                return HttpResponseRedirect(reverse('petmon:store'), context)

        del self.request.session['cart']
        del self.request.session['cart_item']
        del self.request.session['amount']

        context['my_item'] = Repo.objects.filter(owner=owner)

        return HttpResponseRedirect(reverse('petmon:store'), context)


class RepoView(BaseMixin, ListView):
    model = Repo
    template_name = 'petmon/my_repo.html'

    def get_context_data(self, **kwargs):
        context = super(RepoView, self).get_context_data(**kwargs)
        context['object_list'] = Repo.objects.filter(owner=context['log_user'])

        return context
