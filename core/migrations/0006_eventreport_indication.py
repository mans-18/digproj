# Generated by Django 4.2 on 2025-02-02 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_event_kollege_alter_event_persona'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventreport',
            name='indication',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
