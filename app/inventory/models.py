from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')


class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} at {self.address}"


class Ingredient(models.Model):
    ingredient_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    unit = models.CharField(max_length=50)
    cost = models.FloatField()

    def __str__(self):
        return self.name


class Recipe(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    quantity = models.FloatField()
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Modifier(models.Model):
    class ModifierNames(models.TextChoices):
        ADD_INGREDIENT = 'Add ingredient'
        ALLERGENTS = 'Allergens'

    modifier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, choices=ModifierNames.choices)
    option = models.CharField(max_length=50)

    def __str__(self):
        return self.name


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
    staff_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    dob = models.DateField()
    role = models.CharField(max_length=16, choices=StaffRoles.choices)
    iban = models.CharField(max_length=34, validators=[alphanumeric])
    bic = models.CharField(max_length=34, validators=[alphanumeric])
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
