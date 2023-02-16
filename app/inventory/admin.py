from django.contrib import admin

from .models import Location, Recipe, RecipeIngredient, Ingredient, Staff, Menu, Modifier, ModifierOption

admin.site.register(Location)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Staff)
admin.site.register(Menu)
admin.site.register(Modifier)
admin.site.register(ModifierOption)
