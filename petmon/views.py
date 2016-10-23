from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import F, Q
from django.utils import timezone
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.base import ContextMixin

from petmon.forms import LoginForm, PetChooseForm
from petmon.models import User, Pet, Commodity, Repo, Relationship, Request


# Create your views here.
class BaseMixin(ContextMixin):
    # def get_context_data(self, **kwargs):
    def get_context_data(self, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)
        if self.request.user.is_active:
            user = User.objects.get(pk=self.request.user.id)
            context['friend_rank'] = user.friends.order_by('-pet__rank')[:10]
            context['unread_news'] = user.unviewed
        else:
            user = None

        context['log_user'] = user

        return context


# URL name = 'index'
class IndexView(BaseMixin, TemplateView):
    template_name = 'petmon/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data()
        context['users'] = User.objects.all()

        return context


# URL name = 'user_control'
class UserControlView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'signup':
            return render(self.request, 'petmon/signup.html')
        elif slug == 'messages':
            return self.messages(self.request)
        elif slug == 'friends':
            return self.friends(self.request)
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
        elif slug == 'permit_request':
            return self.permit_friend_request(self.request)
        elif slug == 'remove_friend':
            return self.remove_friend(self.request)
        else:
            return HttpResponseRedirect(reverse('petmon:index'))

    def login(self):
        try:
            next_page = self.request.POST['next']
        except KeyError:
            next_page = self.request.META['HTTP_REFERER']

        form = LoginForm(self.request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                self.request.session.set_expiry(0)
                login(self.request, user)

        return HttpResponseRedirect(next_page)

    def logout(self):
        logout(self.request)
        next_page = self.request.META['HTTP_REFERER']

        return HttpResponseRedirect(next_page)

    def signup(self):
        user_name = self.request.POST['username']
        firstname = self.request.POST['firstname']
        lastname = self.request.POST['lastname']
        pwd = self.request.POST['password']
        pwd_confirm = self.request.POST['password_confirm']
        e_mail = self.request.POST['email']
        if pwd == pwd_confirm:
            user = User.objects.create(username=user_name, first_name=firstname, last_name=lastname, email=e_mail)
            user.set_password(pwd)
            try:
                user.save()
                user = authenticate(username=user_name, password=pwd)
                login(self.request, user)
            except Exception:
                pass
        else:
            HttpResponseRedirect(reverse('petmon:usesr_control', kwargs={'slug': 'signup'}))

        # return render(self.request, 'petmon/choose.html')
        return HttpResponseRedirect(reverse('petmon:pet', kwargs={'slug': 'choose'}))

    @method_decorator(login_required)
    def messages(self, request):
        context = self.get_context_data()
        log_user = context['log_user']
        context['messages'] = Request.objects.filter(to_user=log_user, viewed=False)

        return render(self.request, 'petmon/messages.html', context)

    @method_decorator(login_required)
    def friends(self, request):
        context = self.get_context_data()
        log_user = context['log_user']
        context['friends'] = log_user.friends.all()

        return render(self.request, 'petmon/friends.html', context)

    @method_decorator(login_required)
    def permit_friend_request(self, request):
        context = self.get_context_data()
        log_user = context['log_user']
        from_user_id = self.request.POST['from_user_id']
        request = Request.objects.get(from_user_id=from_user_id, to_user_id=log_user.id)
        request.viewed = True
        Relationship.objects.create(from_user_id=log_user.id,
                                    to_user_id=from_user_id,
                                    add_date=timezone.now()
                                    ).save()
        Relationship.objects.create(from_user_id=from_user_id,
                                    to_user_id=log_user.id,
                                    add_date=timezone.now()
                                    ).save()
        request.save()

        if log_user.unviewed > 0:
            log_user.unviewed = F('unviewed') - 1
            log_user.save()

        return HttpResponseRedirect(reverse('petmon:user_control', kwargs={'slug': 'messages'}))

    @method_decorator(login_required)
    def remove_friend(self, request):
        context = self.get_context_data()
        to_user_id = self.request.POST['user_id']
        log_user = context['log_user']
        Relationship.objects.get(from_user=log_user, to_user_id=to_user_id).delete()
        Relationship.objects.get(from_user_id=to_user_id, to_user=log_user).delete()
        try:
            Request.objects.get(from_user=log_user, to_user_id=to_user_id).delete()
        except ObjectDoesNotExist:
            Request.objects.get(from_user_id=to_user_id, to_user=log_user).delete()

        context['friends'] = log_user.friends.all()

        return HttpResponseRedirect(reverse('petmon:user_control', kwargs={'slug': 'friends'}))


# URL name = 'user'
class UserView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'homepage':
            return self.homepage()
        elif slug == 'friend_control':
            user_id = self.kwargs.get('user_id')

            return HttpResponseRedirect(reverse('petmon:user', kwargs={'slug': 'homepage',
                                                                       'user_id': user_id}))
        else:
            raise Http404

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'friend_control':
            return self.send_request(self.request)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data()
        user_id = self.kwargs.get('user_id')

        if User.objects.filter(pk=user_id).exists():
            user = User.objects.get(pk=user_id)
        else:
            raise Http404

        try:
            context['pet'] = user.pet
        except AttributeError:
            pass

        context['owner'] = user
        log_user = context['log_user']
        try:
            relationship = Relationship.objects.get(from_user=log_user, to_user=user)
            context['added_friend'] = True
        except ObjectDoesNotExist:
            try:
                Request.objects.get(from_user=log_user, to_user=user)
                context['added_friend'] = '-1'
            except ObjectDoesNotExist:
                context['added_friend'] = False

        return context

    def homepage(self):
        context = self.get_context_data()

        return render(self.request, 'petmon/pet_info.html', context)

    @method_decorator(login_required)
    def send_request(self, request):
        context = self.get_context_data()
        added_user = context['owner']
        log_user = context['log_user']

        request = Request.objects.create(
            from_user=log_user,
            to_user=added_user,
            send_date=timezone.now()
        )
        request.save()
        added_user.unviewed = F('unviewed') + 1
        added_user.save()

        return HttpResponseRedirect(
            reverse('petmon:user', kwargs={'user_id': added_user.id, 'slug': 'homepage'}))


# URL name = 'my_pet'
class MyPetView(BaseMixin, TemplateView):
    template_name = 'petmon/pet_info.html'

    def get_context_data(self, **kwargs):
        context = super(MyPetView, self).get_context_data()
        user = context['log_user']
        context['owner'] = user

        try:
            context['pet'] = user.pet
        except AttributeError:
            pass

        context['object_list'] = Repo.objects.filter(owner=context['log_user'])
        try:
            context['feed'] = self.request.session['feed_item']
        except KeyError:
            pass

        return context


# URL name = 'pet'
class PetView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'choose':
            context = super(PetView, self).get_context_data()
            return render(self.request, 'petmon/choose.html', context)
        elif slug == 'add_feed':
            return self.add_to_feed(self.request)
        elif slug == 'feed':
            return HttpResponseRedirect(reverse('petmon:my_pet'))
        else:
            raise Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'choose':
            return self.choose_pet(self.request)

        elif slug == 'feed':
            return self.feed_pet(self.request)

        elif slug == 'clean_feed':
            return self.clean_feed_basket()

        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(PetView, self).get_context_data()
        user = context['log_user']
        context['object_list'] = Repo.objects.filter(owner=user)
        context['owner'] = user
        context['pet'] = user.pet

        return context

    @method_decorator(login_required)
    def add_to_feed(self, request):
        item_id = self.request.GET.get('id')

        try:
            count = int(self.request.GET.get('count'))
        except ValueError:
            return HttpResponseRedirect(reverse('petmon:my_pet'))

        try:
            item = Repo.objects.get(pk=item_id)
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('petmon:my_pet'))
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

        return HttpResponseRedirect(reverse('petmon:my_pet'))

    def clean_feed_basket(self):
        del self.request.session['feed']
        del self.request.session['feed_item']

        return HttpResponseRedirect(reverse('petmon:my_pet'))

    @method_decorator(login_required)
    def choose_pet(self, request):
        context = super(PetView, self).get_context_data()
        log_user = context['log_user']
        try:
            log_user.pet
        except Exception:
            form = PetChooseForm(self.request.POST)
            if form.is_valid():
                pet_name = form.cleaned_data['pet_name']
                pet_kind = form.cleaned_data['pet_kind']
                pet = Pet(name=pet_name, kind=pet_kind, owner=log_user)
                pet.assign_attribute()
                pet.save()
            else:
                return HttpResponseRedirect(reverse('petmon:pet', kwargs={'slug': 'choose'}))
        else:
            pass

        return HttpResponseRedirect(reverse('petmon:my_pet'))


@method_decorator(login_required)
def feed_pet(self, request):
    context = self.get_context_data()
    feeds = self.request.session['feed']
    fails = dict()
    user = context['log_user']
    pet = Pet.objects.get(owner=user)

    for k, v in feeds.items():
        item = Repo.objects.get(pk=k)
        satiation, lush, hp, attack, defence, speed = 0, 0, 0, 0, 0, 0
        if item.count >= v:
            satiation += v * item.commodity.satiation
            lush += v * item.commodity.lush
            hp += v * item.commodity.hp
            attack += v * item.commodity.attack
            defence += v * item.commodity.defence
            speed += v * item.commodity.speed
            pet.satiation = F('satiation') + satiation
            pet.lush = F('lush') + lush
            pet.hp = F('hp') + hp
            pet.attack = F('attack') + attack
            pet.defence = F('defence') + defence
            pet.speed = F('speed') + speed
            item.count = F('count') - v

            if pet.satiation > 100:
                pet.satiation = 100

            if pet.lush > 100:
                pet.lush = 100

            if item.count == 0:
                item.delete()
            else:
                item.save()
        else:
            fails[k] = v

    pet.refresh_rank()
    pet.save()
    del self.request.session['feed']
    del self.request.session['feed_item']
    self.request.session.modified = True

    return HttpResponseRedirect(reverse('petmon:my_pet'))  # URL name = 'store'


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


# URL name = 'shop_control'
class BuyView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        context = super(BuyView, self).get_context_data()

        if slug == 'add_to_cart':
            return self.add_to_cart(self.request)
        else:
            raise Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'buy':
            return self.buy(self.request)
        elif slug == 'clean_cart':
            return self.clean_cart()
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(BuyView, self).get_context_data()
        user = context['log_user']
        context['pet'] = user.pet
        context['object_list'] = Commodity.objects.all()

        return context

    @method_decorator(login_required)
    def add_to_cart(self, request):
        comm_id = self.request.GET.get('id')

        try:
            count = int(self.request.GET.get('count'))

            if count <= 0:
                raise ValueError

        except ValueError:

            return HttpResponseRedirect(reverse('petmon:store'))

        try:
            comm = Commodity.objects.get(pk=int(comm_id))
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('petmon:store'))
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

        return HttpResponseRedirect(reverse('petmon:store'))

    def clean_cart(self):
        del self.request.session['cart']
        del self.request.session['cart_item']
        del self.request.session['amount']

        return HttpResponseRedirect(reverse('petmon:store'))

    @method_decorator(login_required)
    def buy(self, request):
        cart = self.request.session['cart']
        context = self.get_context_data()
        owner = context['log_user']
        amount = int(self.request.session['amount'])

        if amount > owner.step:
            context['my_item'] = Repo.objects.filter(owner=owner)
            context['amount'] = amount

            return HttpResponseRedirect(reverse('petmon:store'))
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
                return HttpResponseRedirect(reverse('petmon:store'))

        del self.request.session['cart']
        del self.request.session['cart_item']
        del self.request.session['amount']

        return HttpResponseRedirect(reverse('petmon:store'))


# URL name = 'repo'
class RepoView(BaseMixin, ListView):
    model = Repo
    template_name = 'petmon/my_repo.html'

    def get_context_data(self, **kwargs):
        context = super(RepoView, self).get_context_data(**kwargs)
        context['object_list'] = Repo.objects.filter(owner=context['log_user'])

        return context
