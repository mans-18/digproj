# Generated by Django 4.2 on 2025-01-13 19:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_persona_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='kollege',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_kollege', to='core.kollege'),
        ),
        migrations.AlterField(
            model_name='event',
            name='persona',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_persona', to='core.persona'),
        ),
    ]
