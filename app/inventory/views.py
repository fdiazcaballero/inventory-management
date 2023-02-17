# from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from inventory.models import Staff, Location, Ingredient, IngredientStock, Menu, RecipeIngredient
from django.db import transaction


@api_view(['POST'])
def accept_delivery(request):
    request_data = request.data  # could use somthing like marshmallow to validate request json
    staff = Staff.objects.filter(staff_id=request_data.get('staff_id', -1)).first()
    # only allowed roles for this action
    if not staff or staff.role not in ['Chef', 'Back-of-house']:
        return Response('Missing/wrong staff_id or staff with wrong role', status=status.HTTP_400_BAD_REQUEST)

    # staff can only make this action within a location that they work in
    location = Location.objects.filter(location_id=request_data.get('location_id', -1)).first()
    if not location or not location.staff_set.filter(staff_id=staff.staff_id).exists():
        return Response('Missing location or staff does not work in location', status=status.HTTP_400_BAD_REQUEST)

    delivery = request_data.get('delivery')
    if not delivery or type(delivery) is not list:
        return Response('Missing or wrong delivery', status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # This below code executes inside a transaction.
        for batch in delivery:
            ingredient = Ingredient.objects.filter(ingredient_id=batch.get('ingredient_id')).first()
            if not ingredient or batch.get("units", 0) < 0.0:
                # We should log this, or maybe return a bad request since the ingredient doesn't belong to our catalog
                return Response(
                    'Error: Ingredient not in catalog or negative units',
                    status=status.HTTP_400_BAD_REQUEST
                )

            ingredient_stock, created = IngredientStock.objects.get_or_create(ingredient=ingredient, location=location)
            if created:
                ingredient_stock.units_available = batch.get("units", 0)
            else:
                ingredient_stock.units_available += batch.get("units", 0)

            ingredient_stock.save()

    return Response('Successful process of delivery', status=status.HTTP_200_OK)


@api_view(['POST'])
def take_stock(request):
    request_data = request.data  # could use somthing like marshmallow to validate request json
    staff = Staff.objects.filter(staff_id=request_data.get('staff_id', -1)).first()
    # No need to check for staff roles since according to specs all staff can do this action
    if not staff:
        return Response('Missing/wrong staff_id', status=status.HTTP_400_BAD_REQUEST)

    # staff can only make this action within a location that they work in
    location = Location.objects.filter(location_id=request_data.get('location_id', -1)).first()
    if not location or not location.staff_set.filter(staff_id=staff.staff_id).exists():
        return Response('Missing location or staff does not work in location', status=status.HTTP_400_BAD_REQUEST)

    delivery = request_data.get('take_stock')
    if not delivery or type(delivery) is not list:
        return Response('Missing or wrong take_stock', status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # This below code executes inside a transaction.
        for batch in delivery:
            ingredient = Ingredient.objects.filter(ingredient_id=batch.get('ingredient_id')).first()
            if not ingredient or batch.get("units", 0) < 0.0:
                # We should log this, or maybe return a bad request since the ingredient doesn't belong to our catalog
                return Response(
                    'Error: Ingredient not in catalog or negative units',
                    status=status.HTTP_400_BAD_REQUEST
                )

            ingredient_stock = IngredientStock.objects.filter(ingredient=ingredient, location=location).first()
            if not ingredient_stock:
                # Log this and trigger some alert
                return Response(
                    'Error: Location did not have ingredient in the stock records thus it cannot be decreased',
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif ingredient_stock.units_available < batch.get("units", 0):
                return Response(
                    'Error: We cannot remove more units than we have on records',
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                ingredient_stock.units_available -= batch.get("units", 0)

            ingredient_stock.save()

    return Response('Successful process of take stock', status=status.HTTP_200_OK)


@api_view(['POST'])
def sell_item(request, menu_id):
    request_data = request.data  # could use somthing like marshmallow to validate request json
    staff = Staff.objects.filter(staff_id=request_data.get('staff_id', -1)).first()
    # only allowed roles for this action
    if not staff or staff.role not in ['Front-of-house']:
        return Response('Missing/wrong staff_id or staff with wrong role', status=status.HTTP_400_BAD_REQUEST)

    # staff can only make this action within a location that they work in
    location = Location.objects.filter(location_id=request_data.get('location_id', -1)).first()
    if not location or not location.staff_set.filter(staff_id=staff.staff_id).exists():
        return Response('Missing location or staff does not work in location', status=status.HTTP_400_BAD_REQUEST)

    menu = Menu.objects.filter(menu_id=menu_id).first()
    if not menu or not menu.location.location_id != location.location_id:
        return Response('Missing menu_id or menu not available in location', status=status.HTTP_400_BAD_REQUEST)

    recipe_ingredients = RecipeIngredient.objects.filter(recipe=menu.recipe)
    with transaction.atomic():
        for recipe_ingredient in recipe_ingredients:
            ingredient_stock = IngredientStock.objects.filter(
                ingredient=recipe_ingredient.ingredient, location=location
            ).first()
            if not ingredient_stock or ingredient_stock.units_available < recipe_ingredient.quantity:
                return Response('Not enough ingredients to sell menu item', status=status.HTTP_400_BAD_REQUEST)
            else:
                ingredient_stock.units_available -= recipe_ingredient.quantity
                ingredient_stock.save()

    return Response('Successful menu item sale', status=status.HTTP_200_OK)
