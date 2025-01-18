# Generated by Django 4.2 on 2024-06-26 22:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailFromSite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('mobile', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('body', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('partner', models.CharField(blank=True, max_length=255, null=True)),
                ('start', models.DateTimeField(blank=True)),
                ('color', models.CharField(blank=True, max_length=20, null=True)),
                ('status', models.CharField(blank=True, max_length=20, null=True)),
                ('insurance', models.CharField(blank=True, max_length=100, null=True)),
                ('resourceId', models.CharField(blank=True, max_length=255, null=True)),
                ('addtitle1', models.CharField(blank=True, max_length=100, null=True)),
                ('addtitle2', models.CharField(blank=True, max_length=100, null=True)),
                ('addtitle3', models.CharField(blank=True, max_length=100, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('genericChar1', models.CharField(blank=True, max_length=255, null=True)),
                ('genericChar2', models.CharField(blank=True, max_length=255, null=True)),
                ('genericChar3', models.CharField(blank=True, max_length=255, null=True)),
                ('genericTime1', models.DateTimeField(blank=True, null=True)),
                ('genericNumber1', models.FloatField(blank=True, null=True)),
                ('genericNumber2', models.FloatField(blank=True, null=True)),
                ('genericNumber3', models.FloatField(blank=True, null=True)),
            ],
            options={
                'ordering': ['start'],
            },
        ),
        migrations.CreateModel(
            name='GenericGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gg1', models.CharField(blank=True, max_length=255, null=True)),
                ('gg2', models.CharField(blank=True, max_length=255, null=True)),
                ('gg3', models.CharField(blank=True, max_length=255, null=True)),
                ('gg4', models.CharField(blank=True, max_length=255, null=True)),
                ('gg5', models.FloatField(blank=True, null=True)),
                ('gg6', models.FloatField(blank=True, null=True)),
                ('gg7', models.FloatField(blank=True, null=True)),
                ('gg8', models.TextField(blank=True, null=True)),
                ('gg9', models.BooleanField(blank=True, null=True)),
                ('gg10', models.TextField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['gg1'],
            },
        ),
        migrations.CreateModel(
            name='Procedure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('code', models.CharField(blank=True, max_length=15, null=True, unique=True)),
                ('value1', models.CharField(blank=True, max_length=15, null=True)),
                ('value2', models.CharField(blank=True, max_length=15, null=True)),
                ('value3', models.CharField(blank=True, max_length=25, null=True)),
                ('genericChar', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'code')},
                'index_together': {('name', 'code')},
            },
        ),
        migrations.CreateModel(
            name='Persona',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('mobile', models.CharField(max_length=20)),
                ('whatsapp', models.CharField(blank=True, max_length=20, null=True)),
                ('telephone', models.CharField(blank=True, max_length=20, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('street', models.CharField(blank=True, max_length=255, null=True)),
                ('complement', models.CharField(blank=True, max_length=100, null=True)),
                ('postalcode', models.CharField(blank=True, max_length=20, null=True)),
                ('dob', models.DateField(blank=True, null=True)),
                ('registerdate', models.DateTimeField(null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'mobile')},
                'index_together': {('name', 'mobile')},
            },
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('crm', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('mobile', models.CharField(max_length=20)),
                ('whatsapp', models.CharField(blank=True, max_length=20, null=True)),
                ('telephone', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'ordering': ['name'],
                'index_together': {('name', 'crm')},
            },
        ),
        migrations.CreateModel(
            name='Kollege',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('crm', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('mobile', models.CharField(blank=True, max_length=20)),
            ],
            options={
                'ordering': ['name'],
                'index_together': {('name', 'crm')},
            },
        ),
        migrations.CreateModel(
            name='EventReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('im1', models.TextField(blank=True, null=True)),
                ('im2', models.TextField(blank=True, null=True)),
                ('im3', models.TextField(blank=True, null=True)),
                ('im4', models.TextField(blank=True, null=True)),
                ('im5', models.TextField(blank=True, null=True)),
                ('im6', models.TextField(blank=True, null=True)),
                ('im7', models.TextField(blank=True, null=True)),
                ('im8', models.TextField(blank=True, null=True)),
                ('im9', models.TextField(blank=True, null=True)),
                ('im10', models.TextField(blank=True, null=True)),
                ('drugs', models.CharField(blank=True, max_length=255, null=True)),
                ('anest', models.CharField(blank=True, max_length=255, null=True)),
                ('assistant', models.CharField(blank=True, max_length=255, null=True)),
                ('equipment', models.CharField(blank=True, max_length=255, null=True)),
                ('phar', models.TextField(blank=True, null=True)),
                ('esop', models.TextField(blank=True, null=True)),
                ('stom', models.TextField(blank=True, null=True)),
                ('duod', models.TextField(blank=True, null=True)),
                ('urease', models.CharField(blank=True, max_length=255, null=True)),
                ('biopsy', models.CharField(blank=True, max_length=255, null=True)),
                ('hystoResults', models.CharField(blank=True, max_length=255, null=True)),
                ('prep', models.TextField(blank=True, null=True)),
                ('quality', models.CharField(blank=True, max_length=255, null=True)),
                ('colo', models.TextField(blank=True, null=True)),
                ('genericDescription', models.TextField(blank=True, null=True)),
                ('conc1', models.CharField(blank=True, max_length=255, null=True)),
                ('conc2', models.CharField(blank=True, max_length=255, null=True)),
                ('conc3', models.CharField(blank=True, max_length=255, null=True)),
                ('conc4', models.CharField(blank=True, max_length=255, null=True)),
                ('conc5', models.CharField(blank=True, max_length=255, null=True)),
                ('conc6', models.CharField(blank=True, max_length=255, null=True)),
                ('complications', models.CharField(blank=True, max_length=255, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.event')),
            ],
            options={
                'ordering': ['id', 'assistant'],
            },
        ),
        migrations.AddField(
            model_name='event',
            name='kollege',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.kollege'),
        ),
        migrations.AddField(
            model_name='event',
            name='persona',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events-persona+', to='core.persona'),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('is_limited', models.BooleanField(default=False)),
                ('is_partner', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
