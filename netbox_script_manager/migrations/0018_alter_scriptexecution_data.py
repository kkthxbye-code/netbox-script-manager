# Generated by Django 4.2.4 on 2023-09-05 11:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_script_manager", "0017_alter_scriptexecution_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scriptexecution",
            name="data",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
