from django.contrib import admin

from .models import Location, Recipe, Ingredient, Staff, Menu, Modifier

admin.site.register(Location)
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Staff)
admin.site.register(Menu)
admin.site.register(Modifier)
