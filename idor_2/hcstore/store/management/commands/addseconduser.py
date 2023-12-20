from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):

    def handle(self, *args, **options):
        if User.objects.filter(username=os.getenv('DJANGO_SECONDUSER_USERNAME')).exists():
            print('Seconduser already exists')
        else:
            print('Creating seconduser')
            superuser = User.objects.create_superuser(
                email=os.getenv('DJANGO_SECONDUSER_EMAIL'), 
                username=os.getenv('DJANGO_SECONDUSER_USERNAME'), 
                password=os.getenv('DJANGO_SECONDUSER_PASSWORD')
            )
            superuser.is_active = True
            superuser.is_admin = False
            superuser.save()
