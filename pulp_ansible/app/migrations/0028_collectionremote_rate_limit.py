# Generated by Django 2.2.17 on 2021-01-14 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ansible', '0027_auto_20201120_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectionremote',
            name='rate_limit',
            field=models.IntegerField(null=True),
        ),
    ]