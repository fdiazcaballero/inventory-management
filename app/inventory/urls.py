from django.urls import path

from . import views

urlpatterns = [
    path('ingredient-stock/accept-delivery/', views.accept_delivery, name='accept_delivery'),
    path('ingredient-stock/take-stock/', views.take_stock, name='take_stock'),
    path('menu/<int:menu_id>/sell/', views.sell_item, name='sell_item'),
    path('inventory-report/', views.generate_inventory_report, name='generate_inventory_report'),
    path('finantial-summary/', views.generate_finantial_summary, name='generate_finantial_summary'),
]
