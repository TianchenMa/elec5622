from django.db import models
from django.contrib.auth.models import AbstractUser
from elec5622 import settings

# Create your models here.
GENDER = (
    ('0', u'Male'),
    ('1', u'Female')
)

KIND = (
    ('0', u'Fire'),
    ('1', u'Water'),
    ('2', u'Plant'),
)

ITEM_KIND = (
    ('0', 'food'),
    ('1', 'drink')
)

ATTRIBUTE = {
    '0': {
        'hp': 100,
        'attack': 30,
        'defence': 10,
        'speed': 15,
    },
    '1': {
        'hp': 100,
        'attack': 20,
        'defence': 25,
        'speed': 10,
    },
    '2': {
        'hp': 100,
        'attack': 25,
        'defence': 15,
        'speed': 15,
    }
}


class User(AbstractUser):
    gender = models.CharField(max_length=1, default='0', choices=GENDER)
    step = models.IntegerField(default=0)
    intro = models.CharField(max_length=200, null=True, blank=True)
    friends = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Relationship',
        through_fields=('from_user', 'to_user')
    )

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['id']


class Relationship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='from_user'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='to_user'
    )
    reviewed = models.BooleanField(default=False)
    add_date = models.DateTimeField('Date added.')


class Pet(models.Model):
    name = models.CharField(max_length=50, null=False)
    kind = models.CharField(max_length=1, choices=KIND, default='0')
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    hp = models.IntegerField(null=False)
    attack = models.IntegerField(null=False)
    defence = models.IntegerField(null=False)
    speed = models.IntegerField(null=False)
    satiation = models.IntegerField(null=False, default=100)
    lush = models.IntegerField(null=False, default=100)
    rank = models.IntegerField(null=False)

    def assign_attribute(self):
        self.hp = ATTRIBUTE[self.kind]['hp']
        self.attack = ATTRIBUTE[self.kind]['attack']
        self.defence = ATTRIBUTE[self.kind]['defence']
        self.speed = ATTRIBUTE[self.kind]['speed']
        self.rank = self.hp + self.attack + self.defence + self.speed

    def refresh_rank(self):
        self.rank = self.hp + self.attack + self.defence + self.speed

    class Meta:
        ordering = ['id']


class Commodity(models.Model):
    name = models.CharField(max_length=50, null=False)
    kind = models.CharField(max_length=1, choices=ITEM_KIND, default='0')
    price = models.IntegerField(null=False)
    satiation = models.IntegerField(null=False)
    lush = models.IntegerField(null=False)
    hp = models.IntegerField(null=False)
    attack = models.IntegerField(null=False)
    defence = models.IntegerField(null=False)
    speed = models.IntegerField(null=False)

    class Meta:
        ordering = ['id']


class Repo(models.Model):
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    count = models.IntegerField(null=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']
