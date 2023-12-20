from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView
from .models import Cart, CartItem, Product, Transaction, DEFAULT_CREDIT

import json

class CartDetailView(LoginRequiredMixin, DetailView):
    model = Cart

    def get_queryset(self):
        self.user = get_object_or_404(User, pk=self.request.user.pk)
        queryset = super(CartDetailView, self).get_queryset()
        return queryset.filter(customer=self.user.customer)

class CustomerCreateView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'store/customer_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        #save the new user first
        form.save()
        #get the username and password
        username = self.request.POST['username']
        password = self.request.POST['password1']
        #authenticate user then login
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return HttpResponseRedirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["default_credit"] = DEFAULT_CREDIT
        return context

class ProductListView(ListView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["default_credit"] = DEFAULT_CREDIT
        return context
    
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction

    def get_queryset(self):
        self.user = get_object_or_404(User, pk=self.request.user.pk)
        return Transaction.objects.filter(customer=self.user.customer)

@login_required
def cart_redirect(request):
    if request.method == 'GET':
        user = get_object_or_404(User, pk=request.user.pk)
        if not user.customer.cart:
            user.customer.cart = Cart()
            user.customer.cart.save()
            user.customer.save()
        return redirect('cart_detail', pk=user.customer.cart.pk)
    else:
        return HttpResponseNotAllowed(['GET'])

@login_required
def add_product_to_cart(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        try:
            body_data = json.loads(body_unicode)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'The object is not a valid JSON.'})
        if 'product' in body_data.keys() and 'quantity' in body_data.keys():
            try:
                product = Product.objects.get(pk=body_data['product'])
            except:
                return JsonResponse({'error': 'The product does not exist.'})            
            user = get_object_or_404(User, pk=request.user.pk)
            if not user.customer.cart:
                user.customer.cart = Cart()
                user.customer.cart.save()
                user.customer.save()
            cart = user.customer.cart
            try:
                cartitem = CartItem.objects.get(product=product, cart=cart)
                cartitem.quantity = cartitem.quantity + body_data['quantity']
            except CartItem.DoesNotExist:
                cartitem = CartItem(product=product, cart=cart, quantity=body_data['quantity'])            
            cartitem.save()
            cart.quantity = update_cart_quantity(cart)
            cart.total = update_cart_total(cart)
            cart.save()
            return JsonResponse({'cartTotal': cart.quantity})
        else:
            return HttpResponse(status=400)
    else:
        return HttpResponseNotAllowed(['POST'])

@login_required
def delete_product_from_cart(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        try:
            body_data = json.loads(body_unicode)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'The object is not a valid JSON.'})
        if 'product' in body_data.keys():
            try:
                product = Product.objects.get(pk=body_data['product'])
            except:
                return JsonResponse({'error': 'The product does not exist.'})
            user = get_object_or_404(User, pk=request.user.pk)
            if not user.customer.cart:
                return JsonResponse({'error': 'User does not have a cart. Did you try adding products to the cart?'})
            cart = user.customer.cart
            try:
                cartitem = CartItem.objects.get(product=product, cart=cart)
                cartitem.delete()
            except CartItem.DoesNotExist:
                return JsonResponse({'error': 'Product not in cart.'})
            cart.quantity = update_cart_quantity(cart)
            cart.total = update_cart_total(cart)
            cart.save()
            return JsonResponse({'cartQuantity': cart.quantity, 'cartTotal': cart.total})
        else:
            return HttpResponse(status=400)
    else:
        return HttpResponseNotAllowed(['POST'])

@login_required
def update_product_in_cart(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        try:
            body_data = json.loads(body_unicode)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'The object is not a valid JSON.'})
        if 'product' in body_data.keys() and 'quantity' in body_data.keys():
            if body_data['quantity'] == 0:
                return JsonResponse({'error': 'Quantity cannot be 0.'})
            try:
                product = Product.objects.get(pk=body_data['product'])
            except:
                return JsonResponse({'error': 'The product does not exist.'})            
            user = get_object_or_404(User, pk=request.user.pk)
            if not user.customer.cart:
                return JsonResponse({'error': 'User does not have a cart. Did you try adding products to the cart?'})
            cart = user.customer.cart
            try:
                cartitem = CartItem.objects.get(product=product, cart=cart)
                cartitem.quantity = body_data['quantity']
            except CartItem.DoesNotExist:
                return JsonResponse({'error': 'Product not in cart.'})         
            cartitem.save()
            cart.quantity = update_cart_quantity(cart)
            cart.total = update_cart_total(cart)
            cart.save()
            return JsonResponse({'cartQuantity': cart.quantity, 'cartTotal': cart.total})
        else:
            return HttpResponse(status=400)
    else:
        return HttpResponseNotAllowed(['POST'])


@login_required
def place_order(request):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=request.user.pk)
        if user.customer.credit >= user.customer.cart.total:
            transaction = Transaction(customer=user.customer, cart=user.customer.cart)
            user.customer.credit = user.customer.credit - user.customer.cart.total
            transaction.save()
            user.customer.cart = Cart()
            user.customer.cart.save()
            user.customer.save()
            return redirect('orders')
        else:
            return JsonResponse({'error': 'You don\'t have enough credits.'})
    else:
        return HttpResponseNotAllowed(['POST'])


# Helper functions

def update_cart_quantity(cart):
    quantity = CartItem.objects.filter(cart=cart).aggregate(Sum('quantity'))['quantity__sum']
    if quantity:
        return quantity
    else:
        return 0

def update_cart_total(cart):
    total = 0
    for cartitem in CartItem.objects.filter(cart=cart):
        total = total + cartitem.product.price * cartitem.quantity
    return total