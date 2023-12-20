from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

import hashlib

DEFAULT_CREDIT = 10.00

class Cart(models.Model):
    quantity = models.IntegerField(default=0)
    total = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)

    def __str__(self):
        if hasattr(self, 'customer'):
            return "Cart ID: {pk}; Customer: {customer}".format(pk=self.pk, customer=self.customer)
        else:
            return "Cart ID: {pk}; Customer: none".format(pk=self.pk) 

class Product(models.Model):
    name = models.CharField(max_length=31)
    description = models.CharField(max_length=255)
    price = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    flag = models.CharField(max_length=63, null=True, blank=True)
    image = models.CharField(max_length=63, null=True, blank=True)

    def __str__(self):
        return self.name

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return "Product: {product}; Quantity: {quantity}; Cart: {{{cart}}}".format(product=self.product, quantity=self.quantity, cart=self.cart)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    credit = models.DecimalField(default=DEFAULT_CREDIT, max_digits=10, decimal_places=2)
    cart = models.OneToOneField(Cart, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return "{user}".format(user=self.user)

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_customer(sender, instance, **kwargs):
    instance.customer.save()

class Transaction(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    slug = models.SlugField(default='', editable=False, max_length=255)

    def get_absolute_url(self):
        kwargs = {'pk': self.id,'slug': self.slug}
        return reverse('order', kwargs=kwargs)

@receiver(post_save, sender=Transaction)
def update_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = hashlib.md5(str(instance.pk).encode("utf")).hexdigest()
        instance.save()
    else:
        pass