from django.contrib import admin

from petmon.models import User, Pet


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    fields = [
        'username',
        'gender',
        'step',
        'intro',
    ]

    list_display = ['username', 'gender', 'step']


class PetAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'owner',
        'kind',
        'hp',
        'attack',
        'defence',
        'speed',
    ]

    list_display = ('name', 'owner', 'kind')

admin.site.register(User, UserAdmin)
admin.site.register(Pet, PetAdmin)
