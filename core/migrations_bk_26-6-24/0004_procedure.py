# Generated by Django 4.2 on 2024-06-26 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_user_options_user_is_partner_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Procedure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('code', models.CharField(blank=True, max_length=15, null=True, unique=True)),
                ('value', models.CharField(blank=True, max_length=15, null=True)),
                ('kollegePart', models.CharField(blank=True, max_length=15, null=True)),
                ('businessPart', models.CharField(blank=True, max_length=15, null=True)),
                ('genericChar', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'code')},
                'index_together': {('name', 'code')},
            },
        ),
    ]