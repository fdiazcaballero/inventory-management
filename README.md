# Inventory management app

## About

I have chosen Django to develop this app. Normally I would have chosen a much faster and lightweight
framework to develop an API such as Flask, or FastAPI. And then develop a separated React frontend to consume the API.
But given the short time allowed and realizing that no front-end work will be possible, I decided to use Django so 
that at least the models and their data could be visualized on a browser in the Django admin backoffice.


For this MVP I have prioritized:

- Develop all features requested 
- Have a good db schema
- Have a dockerized app possible to run in any machine
- Import the data dump provided

Time constraints have made to de-prioritize the followings aspects for this MVP: (aka things missing)

- Missing a proper front end. However, a word around is provided with the Admin backoffice.
- Unit testing. Normally I love to be as close as possible to TDD, but to produce something meaningful I had to save time on this :(
- Security: de-prioritized on MVP given that "The app will not be public facing, it should not be shared across locations. Each site has secure Wi-Fi and staff will access the store’s system using a mobile web browser via a local IP address."
- Proper logging and exceptions handling.
- Some code in the views file could be more DRY but no time to refactor that
- Endpoints should not get staff id in the body but user should be logged in and sending token on auth headers
- Reports endpoints should be a get and not a post with the manager logged in and sending auth headers
- Missing online api documentation tool
- Missing prod dockerfile and prod docker compose using gunicorn and nginx


## How to run on development containers

This can be run in any Unix, Windows, or MacOS machine. 
The only requirement is to have [Docker](https://docs.docker.com/engine/install/) installed.

```
git clone git@github.com:fdiazcaballero/inventory-management.git
cd inventory-management
cp .env.dev-sample .env.dev
docker compose up -d --build
```

Note that in the entry point of the Dockerfile I'm running already 
the migrations and running a Django command that I created to import to the db 
the "Weird Salads - Data Export" file that was provided. So after running the above
the app should be in the desired initial state.
See file (app/inventory/management/commands/import.py)
Also flake and the unit tests are run as part of the build in the Dockerfile.


Try [http://localhost:8000/ping](http://localhost:8000/ping)

You can run the following command to create an admin superuser:
```commandline
docker compose exec web python manage.py createsuperuser 
```

Then you can log in the admin space in [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
There you will be able to inspect the models. For example for Locations: [http://127.0.0.1:8000/admin/inventory/location/](http://127.0.0.1:8000/admin/inventory/location/)

## Happy flow to verify that the app works

After you have successfully built the application with the commands above.
You can now run the bellow command to test that the main requirements for the app work.

1. Accept deliveries:

Note: we'll add enough of needed ingredients to be able to sell menu item 1 later on.
```commandline
curl --location --request POST 'http://localhost:8000/inventory/ingredient-stock/accept-delivery/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "staff_id": 65,
    "location_id": 21,
    "delivery": [
        {
            "ingredient_id": 403,
            "units": 50            
        },
        {
            "ingredient_id": 409,
            "units": 50
        },
        {
            "ingredient_id": 92,
            "units": 50
        },
        {
            "ingredient_id": 440,
            "units": 50
        },
        {
            "ingredient_id": 19,
            "units": 50
        },
        {
            "ingredient_id": 205,
            "units": 50
        }
    ]
}'
```
You can use the admin [http://127.0.0.1:8000/admin/inventory/ingredientstock/](http://127.0.0.1:8000/admin/inventory/ingredientstock/)
to verify that the ingredients are now in stock.

2. Take stock

Let's throw away some waste that came with the previous delivery 
(don't worry we'll have enough left to sell our menu 1)
```commandline
curl --location --request POST 'http://localhost:8000/inventory/ingredient-stock/take-stock/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "staff_id": 10,
    "location_id": 21,
    "take_stock": [
        {
            "ingredient_id": 403,
            "units": 1            
        },
        {
            "ingredient_id": 409,
            "units": 1
        }
    ]
}'
```
Verify at [http://127.0.0.1:8000/admin/inventory/ingredientstock/](http://127.0.0.1:8000/admin/inventory/ingredientstock/)
that some quantities have decreased accordingly.

3. Sell items

Now let's sell a menu item

```commandline
curl --location --request POST 'http://localhost:8000/inventory/menu/1/sell/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "staff_id": 10,
    "location_id": 21
}'
```

Verify at [http://127.0.0.1:8000/admin/inventory/ingredientstock/](http://127.0.0.1:8000/admin/inventory/ingredientstock/)
that the menu's recipe quantities have been taken off the stock.

4. Pull reports

After the previous actions now we have some data for our reports:

- Inventory report: Get all the inventory movements in a period for a given location.
```commandline
curl --location --request POST 'http://localhost:8000/inventory/inventory-report/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "staff_id": 225,
    "location_id": 21,
    "start_date": "01/01/2023",
    "end_date": "28/02/2023"
}'
```
You should get the csv report data in console, or you can save into a csv file if you're using Postman
But you can also check the model in the admin [http://127.0.0.1:8000/admin/inventory/stockaudit/](http://127.0.0.1:8000/admin/inventory/stockaudit/)

- Financial report: containing for the selected period
  - total cost of all deliveries
  - total revenue from all sales
  - total value of current inventory (at the request time)
  - cost of all recorded waste

```commandline
curl --location --request POST 'http://localhost:8000/inventory/finantial-summary/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "staff_id": 225,
    "location_id": 21,
    "start_date": "01/01/2023",
    "end_date": "28/02/2023"
}'
```
Again you should get the csv in the console. 
These are figures computed on real time so there is no equivalent model for them.
However, an interesting model to check is the Sales Audit [http://127.0.0.1:8000/admin/inventory/salesaudit/](http://127.0.0.1:8000/admin/inventory/salesaudit/)

This is a happy flow but there are endless combinations where the staff doesn't have the correct role
or doesn't work in a location, the ingredient stock is low to sell a menu, etc, etc that will produce errors as expected. 
Please feel free to play with it and maybe break it! :)
