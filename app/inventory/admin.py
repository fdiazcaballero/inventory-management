from django.contrib import admin

from .models import Location, Recipe, RecipeIngredient, Ingredient,\
    IngredientStock, Staff, Menu, Modifier, ModifierOption, StockAudit, SalesAudit

admin.site.register(Location)
admin.site.register(Ingredient)
admin.site.register(IngredientStock)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Staff)
admin.site.register(Menu)
admin.site.register(Modifier)
admin.site.register(ModifierOption)
admin.site.register(StockAudit)
admin.site.register(SalesAudit)
