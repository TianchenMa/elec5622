from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from petmon.views import UserControlView, PetView, StoreView, BuyView, RepoView, MyPetView, UserView
from petmon.views import IndexView


app_name = 'petmon'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

    # url(r'^auth/', include('django.contrib.auth.urls')),

    url(r'^auth/login/$', auth_views.login, {'template_name': 'petmon/login.html'}),

    url(r'^(?P<slug>\w+)$', UserControlView.as_view(), name='user_control'),

    url(r'^(?P<user_id>[0-9]+)/(?P<slug>\w+)$', UserView.as_view(), name='user'),

    url(r'^pet/$', MyPetView.as_view(), name='my_pet'),

    url(r'^pet/(?P<slug>\w+)$', PetView.as_view(), name='pet'),

    url(r'^store/$', StoreView.as_view(), name='store'),

    url(r'^store/(?P<slug>\w+)$', BuyView.as_view(), name='shop_control'),

    url(r'^my_repo/$', RepoView.as_view(), name='repo')
]