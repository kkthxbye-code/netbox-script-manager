# Generated by Django 4.1.9 on 2023-07-06 07:38

import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0092_delete_jobresult"),
        ("netbox_script_manager", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="scriptinstance",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
        migrations.AddField(
            model_name="scriptinstance",
            name="tags",
            field=taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
        ),
    ]
