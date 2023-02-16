# from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from inventory.models import Staff, Location, Ingredient, IngredientStock
from django.db import transaction


@api_view(['POST'])
def accept_delivery(request):
    request_data = request.data  # could use somthing like marshmallow to validate request json
    staff = Staff.objects.filter(staff_id=request_data.get('staff_id', -1)).first()
    # only allowed roles for this action
    if not staff or staff.role not in ['Chef', 'Back-of-house']:
        return Response('Missing staff or staff with wrong role', status=status.HTTP_400_BAD_REQUEST)

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
            if not ingredient:
                # We should log this, or maybe return a bad request since the ingredient doesn't belong to our catalog
                return Response('Wrong delivery item', status=status.HTTP_400_BAD_REQUEST)

            ingredient_stock, created = IngredientStock.objects.get_or_create(ingredient=ingredient, location=location)
            if created:
                ingredient_stock.units_available = batch.get("units", 0)
            else:
                ingredient_stock.units_available += batch.get("units", 0)

            ingredient_stock.save()

    return Response('Successful process of delivery', status=status.HTTP_200_OK)
