# from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from inventory.models import Staff, Location, Ingredient, IngredientStock, Menu, RecipeIngredient, StockAudit, SalesAudit
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Sum
import csv


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
            batch_units = batch.get("units", 0)
            if not ingredient or batch_units < 0.0:
                # We should log this, or maybe return a bad request since the ingredient doesn't belong to our catalog
                return Response(
                    'Error: Ingredient not in catalog or negative units',
                    status=status.HTTP_400_BAD_REQUEST
                )

            ingredient_stock, created = IngredientStock.objects.get_or_create(ingredient=ingredient, location=location)
            if created:
                ingredient_stock.units_available = batch_units
            else:
                ingredient_stock.units_available += batch_units
            ingredient_stock.save()

            stock_audit = StockAudit(
                reason='delivery',
                units_change=batch_units,
                cost=batch_units * ingredient.cost,
                ingredient=ingredient,
                location=location,
                staff=staff
            )
            stock_audit.save()

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
            batch_units = batch.get("units", 0)
            if not ingredient or batch_units < 0.0:
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
            if ingredient_stock.units_available < batch_units:
                return Response(
                    'Error: We cannot remove more units than we have on records',
                    status=status.HTTP_400_BAD_REQUEST
                )

            ingredient_stock.units_available -= batch_units
            ingredient_stock.save()
            stock_audit = StockAudit(
                reason='waste',
                units_change=(-1) * batch_units,  # a negative change
                cost=batch_units * ingredient.cost,
                ingredient=ingredient,
                location=location,
                staff=staff
            )
            stock_audit.save()

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
    if not menu or not menu.location.location_id == location.location_id:
        return Response('Missing menu_id or menu not available in location', status=status.HTTP_400_BAD_REQUEST)

    recipe_ingredients = RecipeIngredient.objects.filter(recipe=menu.recipe)
    with transaction.atomic():
        for recipe_ingredient in recipe_ingredients:
            ingredient_stock = IngredientStock.objects.filter(
                ingredient=recipe_ingredient.ingredient, location=location
            ).first()
            if not ingredient_stock or ingredient_stock.units_available < recipe_ingredient.quantity:
                return Response('Not enough ingredients to sell menu item', status=status.HTTP_400_BAD_REQUEST)

            ingredient_stock.units_available -= recipe_ingredient.quantity
            ingredient_stock.save()
            stock_audit = StockAudit(
                reason='sale',
                units_change=(-1) * (recipe_ingredient.quantity),  # a negative change
                cost=(recipe_ingredient.quantity) * (recipe_ingredient.ingredient.cost),
                ingredient=recipe_ingredient.ingredient,
                location=location,
                staff=staff
            )
            stock_audit.save()

        sale_audit = SalesAudit(sale_amount=menu.price, location=location, menu=menu, staff=staff)
        sale_audit.save()

    return Response('Successful menu item sale', status=status.HTTP_200_OK)


@api_view(['POST'])
def generate_inventory_report(request):
    request_data = request.data  # could use something like marshmallow to validate request json
    staff = Staff.objects.filter(staff_id=request_data.get('staff_id', -1)).first()
    # only allowed roles for this action
    if not staff or staff.role not in ['Manager']:
        return Response('Missing/wrong staff_id or staff with wrong role', status=status.HTTP_400_BAD_REQUEST)

    # staff can only make this action within a location that they work in
    location = Location.objects.filter(location_id=request_data.get('location_id', -1)).first()
    if not location or not location.staff_set.filter(staff_id=staff.staff_id).exists():
        return Response('Missing location or staff does not work in location', status=status.HTTP_400_BAD_REQUEST)

    tz = timezone.get_current_timezone()
    start_date = datetime.strptime(request_data.get('start_date'), '%d/%m/%Y')
    timezone_start_date = timezone.make_aware(start_date, tz, True)
    end_date = datetime.strptime(request_data.get('end_date'), '%d/%m/%Y')
    timezone_end_date = timezone.make_aware(end_date, tz, True)

    stock_audit = StockAudit.objects.filter(location=location, created_at__range=(timezone_start_date, timezone_end_date))

    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f"attachment; filename=inventory_report_{int(round(datetime.now().timestamp()))}.csv"},
    )

    writer = csv.writer(response)
    writer.writerow(['stock_audit_id', 'reason', 'cost', 'ingredient_id', 'staff_id', 'created_at'])
    stock_audit_vals = stock_audit.values_list('stock_audit_id', 'reason', 'cost', 'ingredient_id', 'staff_id', 'created_at')
    for stock_audit_row in stock_audit_vals:
        writer.writerow(stock_audit_row)

    return response


@api_view(['POST'])
def generate_finantial_summary(request):
    request_data = request.data  # could use something like marshmallow to validate request json
    staff = Staff.objects.filter(staff_id=request_data.get('staff_id', -1)).first()
    # only allowed roles for this action
    if not staff or staff.role not in ['Manager']:
        return Response('Missing/wrong staff_id or staff with wrong role', status=status.HTTP_400_BAD_REQUEST)

    # staff can only make this action within a location that they work in
    location = Location.objects.filter(location_id=request_data.get('location_id', -1)).first()
    if not location or not location.staff_set.filter(staff_id=staff.staff_id).exists():
        return Response('Missing location or staff does not work in location', status=status.HTTP_400_BAD_REQUEST)

    tz = timezone.get_current_timezone()
    start_date = datetime.strptime(request_data.get('start_date'), '%d/%m/%Y')
    timezone_start_date = timezone.make_aware(start_date, tz, True)
    end_date = datetime.strptime(request_data.get('end_date'), '%d/%m/%Y')
    timezone_end_date = timezone.make_aware(end_date, tz, True)

    stock_audit = StockAudit.objects.filter(location=location, created_at__range=(timezone_start_date, timezone_end_date))
    sales_audit = SalesAudit.objects.filter(location=location, created_at__range=(timezone_start_date, timezone_end_date))
    ingredient_stock = IngredientStock.objects.filter(location=location)
    total_revenue = sales_audit.aggregate(Sum('sale_amount'))
    total_deliveries_cost = stock_audit.filter(reason='delivery').aggregate(Sum('cost'))
    total_waste_cost = stock_audit.filter(reason='waste').aggregate(Sum('cost'))
    current_inventory_value = 0
    for ingredient in ingredient_stock:
        current_inventory_value += ingredient.units_available * (ingredient.ingredient.cost)

    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f"attachment; filename=finantial_summary_{int(round(datetime.now().timestamp()))}.csv"},
    )

    writer = csv.writer(response)
    writer.writerow([
        'location_id',
        'period',
        'total revenue from sales (in period)',
        'total deliveries cost (in period)',
        'total waste cost (in period)',
        f"current inventory value ({datetime.today().strftime('%d-%m-%Y')})"]
    )

    writer.writerow([
        location.location_id,
        f"{request_data.get('start_date')} to {request_data.get('end_date')}",
        total_revenue['sale_amount__sum'],
        total_deliveries_cost['cost__sum'],
        total_waste_cost['cost__sum'],
        current_inventory_value
    ])

    return response
