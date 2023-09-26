# Generated by Django 4.1.10 on 2023-08-28 06:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_script_manager", "0011_scriptinstance_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="scriptinstance",
            name="weight",
            field=models.PositiveSmallIntegerField(default=1000),
        ),
    ]
