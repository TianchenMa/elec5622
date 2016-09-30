from django.conf.urls import url

from petmon.views import UserControlView, PetView
from petmon.views import IndexView
from . import views


app_name = 'petmon'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

    url(r'^(?P<slug>\w+)$', UserControlView.as_view(), name='user_control'),

    url(r'^pet/(?P<slug>\w+)$', PetView.as_view(), name='pet')
]