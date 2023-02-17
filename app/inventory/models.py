from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')


class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return f"{self.name} at {self.address}"


class Ingredient(models.Model):
    class IngredientUnit(models.TextChoices):
        MILILITER = 'mililiter'
        CENTILITER = 'centiliter'
        DECILITER = 'deciliter'
        LITER = 'liter'

    ingredient_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=16, choices=IngredientUnit.choices)
    cost = models.FloatField()

    def __str__(self):
        return self.name


class IngredientStock(models.Model):

    ingredient_stock_id = models.AutoField(primary_key=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    units_available = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.units_available} {self.ingredient.unit} of {self.ingredient.name} at {self.location.name}"

    class Meta:
        db_table = 'inventory_ingredient_stock'
        unique_together = ('ingredient', 'location',)


class Recipe(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe_ingredient_id = models.AutoField(primary_key=True)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    quantity = models.FloatField()

    def __str__(self):
        return f"{self.ingredient.name} in the {self.recipe.name}"

    class Meta:
        db_table = 'inventory_recipe_ingredient'


class Modifier(models.Model):
    modifier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True)

    def __str__(self):
        return self.name


class ModifierOption(models.Model):
    modifier_option_id = models.AutoField(primary_key=True)
    modifier = models.ForeignKey(Modifier, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, blank=True, null=True)
    option = models.CharField(max_length=50)
    price = models.FloatField()

    def __str__(self):
        return self.recipe.option

    class Meta:
        db_table = 'inventory_modifier_option'


class Menu(models.Model):
    menu_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    price = models.FloatField()
    modifier = models.ForeignKey(Modifier, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.recipe.name} at {self.location.name}"


class Staff(models.Model):
    class StaffRoles(models.TextChoices):
        BACK_OF_HOUSE = 'Back-of-house'
        CHEF = 'Chef'
        FRONT_OF_HOUSE = 'Front-of-house'
        MANAGER = 'Manager'
    staff_id = models.IntegerField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    dob = models.DateField()
    role = models.CharField(max_length=16, choices=StaffRoles.choices)
    iban = models.CharField(max_length=34, validators=[alphanumeric], unique=True)
    bic = models.CharField(max_length=34, validators=[alphanumeric])
    location = models.ManyToManyField(Location)

    def __str__(self):
        return self.name


class StockAudit(models.Model):
    class StockAuditReason(models.TextChoices):
        DELIVERY = 'delivery'
        SALE = 'sale'
        WASTE = 'waste'

    stock_audit_id = models.AutoField(primary_key=True)
    reason = models.CharField(max_length=16, choices=StockAuditReason.choices, editable=False)
    # Prevent deletion of the referenced objects, should use soft deletes
    location = models.ForeignKey(Location, on_delete=models.PROTECT, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, editable=False)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, editable=False)
    units_change = models.FloatField(editable=False)
    # We need this calculation in real time beacuse the cost of an ingredient can vary over time
    cost = models.FloatField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_stock_audit'


class SalesAudit(models.Model):
    sales_audit_id = models.AutoField(primary_key=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, editable=False)
    menu = models.ForeignKey(Menu, on_delete=models.PROTECT, editable=False)
    # We need this calculation in real time beacuse the cost of an ingredient can vary over time
    sale_amount = models.FloatField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_sale_audit'
