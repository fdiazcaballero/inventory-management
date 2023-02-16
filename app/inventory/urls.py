from django.urls import path

from . import views

urlpatterns = [
    path('ingredient_stock/accept_delivery/', views.accept_delivery, name='accept_delivery'),
]
