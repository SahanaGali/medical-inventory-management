# Generated by Django 5.0 on 2024-06-28 06:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shopapp', '0008_alter_opportunity_customer_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opportunity',
            name='customer_name',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='customer_name',
        ),
    ]
