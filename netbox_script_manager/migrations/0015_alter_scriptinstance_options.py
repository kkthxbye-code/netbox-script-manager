# Generated by Django 4.2.4 on 2023-09-04 08:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_script_manager", "0014_scriptexecution_task_queue"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="scriptinstance",
            options={"ordering": ("group", "weight", "name")},
        ),
    ]
