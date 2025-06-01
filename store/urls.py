from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name="homepage"),
    path('product/<int:id>', index),
    path('cart', index),
    path('checkout', index),
    path('register', index),
    path('login', index),
    path('activate/<str:uid>/<str:token>', index),
    path('reset-password', index),
    path('google/', index),
    path('facebook', index),
    path('password/reset/confirm/<str:uid>/<str:token>', index),
    path('about', index),
]
