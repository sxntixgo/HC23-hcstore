from django.contrib.auth import views as auth_views
from django.urls import path
from .views import CartDetailView, CustomerCreateView, ProductListView, TransactionListView, TransactionDetailView, cart_redirect, add_product_to_cart, delete_product_from_cart, update_product_in_cart, place_order

urlpatterns = [
    path('', ProductListView.as_view(), name='home'),
    path('cart', cart_redirect, name='cart'),
    path('cart/<int:pk>', CartDetailView.as_view(), name='cart_detail'),
    path('cart/addto', add_product_to_cart, name='add_to_cart'),
    path('cart/deletefrom', delete_product_from_cart, name='delete_from_cart'),
    path('cart/updatein', update_product_in_cart, name='update_in_cart'),
    path('login', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('order/<int:pk>-<str:slug>', TransactionDetailView.as_view(), name='order'),
    path('order/place', place_order, name='place_order'),
    path('orders', TransactionListView.as_view(), name='orders'),
    path('register', CustomerCreateView.as_view(), name='register'),
]