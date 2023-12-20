from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):

    def handle(self, *args, **options):
        if User.objects.filter(username=os.getenv('DJANGO_SUPERUSER_USERNAME')).exists():
            print('Superuser already exists')
        else:
            print('Creating superuser')
            superuser = User.objects.create_superuser(
                email=os.getenv('DJANGO_SUPERUSER_EMAIL'), 
                username=os.getenv('DJANGO_SUPERUSER_USERNAME'), 
                password=os.getenv('DJANGO_SUPERUSER_PASSWORD')
            )
            superuser.is_active = True
            superuser.is_admin = True
            superuser.save()
