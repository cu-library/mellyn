# Generated by Django 3.0.4 on 2020-04-29 23:38

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_bleach.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Agreement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300, unique=True)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the agreement.', max_length=300, unique=True, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
                ('body', django_bleach.models.BleachField(help_text='HTML content of the Agreement. The following tags are allowed: h3, p, a, abbr, cite, code, small, em, strong, sub, sup, u, ul, ol, li.')),
                ('created', models.DateField(auto_now=True)),
                ('redirect_url', models.URLField(help_text="URL where patrons will be redirected to after signing the agreement. It must start with 'https://'.", validators=[django.core.validators.URLValidator(code='need_https', message="Enter a valid URL. It must start with 'https://'.", schemes=['https'])])),
                ('redirect_text', models.CharField(help_text='The text of the URL redirect link.', max_length=300)),
                ('hidden', models.BooleanField(default=False, help_text='Hidden agreements do not appear in the list of active agreements.')),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the department.', max_length=300, unique=True, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
            ],
        ),
        migrations.CreateModel(
            name='Faculty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, unique=True)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the faculty.', max_length=300, unique=True, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, unique=True)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the resource.', max_length=300, unique=True, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
                ('description', django_bleach.models.BleachField(blank=True, help_text='An HTML description of the resource. The following tags are allowed: h3, p, a, abbr, cite, code, small, em, strong, sub, sup, u, ul, ol, li.')),
            ],
        ),
        migrations.CreateModel(
            name='Signature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=300)),
                ('first_name', models.CharField(blank=True, max_length=300)),
                ('last_name', models.CharField(blank=True, max_length=300)),
                ('email', models.CharField(max_length=200, validators=[django.core.validators.EmailValidator()])),
                ('signed_at', models.DateTimeField(auto_now_add=True)),
                ('agreement', models.ForeignKey(limit_choices_to={'hidden': False}, on_delete=django.db.models.deletion.CASCADE, to='agreements.Agreement')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agreements.Department')),
                ('signatory', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='department',
            name='faculty',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agreements.Faculty'),
        ),
        migrations.AddField(
            model_name='agreement',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agreements.Resource'),
        ),
        migrations.AddConstraint(
            model_name='signature',
            constraint=models.UniqueConstraint(fields=('agreement', 'signatory'), name='unique_signature'),
        ),
    ]
