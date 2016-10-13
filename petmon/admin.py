from django.contrib import admin

from petmon.models import User, Pet, Commodity


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
        'satiation',
        'lush',
        'hp',
        'attack',
        'defence',
        'speed',
    ]

    list_display = ('name', 'owner', 'kind')


class CommodityAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'kind',
        'price',
        'satiation',
        'lush',
        'hp',
        'attack',
        'defence',
        'speed',
    ]

    list_display = ('name', 'kind', 'price')


admin.site.register(User, UserAdmin)
admin.site.register(Pet, PetAdmin)
admin.site.register(Commodity, CommodityAdmin)
