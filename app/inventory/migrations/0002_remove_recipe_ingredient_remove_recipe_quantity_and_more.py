# Generated by Django 4.1.5 on 2023-02-15 16:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='ingredient',
        ),
        migrations.RemoveField(
            model_name='recipe',
            name='quantity',
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('recipe_ingredient_id', models.AutoField(primary_key=True, serialize=False)),
                ('quantity', models.FloatField()),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.ingredient')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.recipe')),
            ],
            options={
                'db_table': 'inventory_recipe_ingredient',
            },
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(through='inventory.RecipeIngredient', to='inventory.ingredient'),
        ),
    ]
