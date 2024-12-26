# Generated by Django 4.2 on 2024-05-27 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_is_limited_alter_persona_registerdate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='user',
            name='is_partner',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False),
        ),
    ]