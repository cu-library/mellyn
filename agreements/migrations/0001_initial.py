# Generated by Django 3.0.4 on 2020-05-06 01:28

import agreements.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import django.utils.timezone
import django_bleach.models
import simple_history.models


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
                ('created', models.DateField(auto_now_add=True)),
                ('start', models.DateTimeField(default=django.utils.timezone.now, help_text='The agreement is valid starting at this date and time. Format (UTC timezone): YYYY-MM-DD HH:MM:SS')),
                ('end', models.DateTimeField(blank=True, default=agreements.models.date_121_days_from_now, help_text='The agreement is valid until this date and time. Format (UTC timezone): YYYY-MM-DD HH:MM:SS', null=True)),
                ('body', django_bleach.models.BleachField(help_text='HTML content of the agreement. The following tags are allowed: h3, p, a, abbr, cite, code, small, em, strong, sub, sup, u, ul, ol, li. Changing this field after the agreement has been signed by patrons is strongly discouraged.')),
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
        migrations.CreateModel(
            name='LicenseCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=300)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agreements.Resource')),
                ('signature', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='license_code', to='agreements.Signature')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalSignature',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('username', models.CharField(max_length=300)),
                ('first_name', models.CharField(blank=True, max_length=300)),
                ('last_name', models.CharField(blank=True, max_length=300)),
                ('email', models.CharField(max_length=200, validators=[django.core.validators.EmailValidator()])),
                ('signed_at', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('agreement', models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'hidden': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='agreements.Agreement')),
                ('department', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='agreements.Department')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('signatory', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical signature',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalResource',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=300)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the resource.', max_length=300, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
                ('description', django_bleach.models.BleachField(blank=True, help_text='An HTML description of the resource. The following tags are allowed: h3, p, a, abbr, cite, code, small, em, strong, sub, sup, u, ul, ol, li.')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical resource',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalLicenseCode',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('code', models.CharField(max_length=300)),
                ('added', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='agreements.Resource')),
                ('signature', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='agreements.Signature')),
            ],
            options={
                'verbose_name': 'historical license code',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalFaculty',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=300)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the faculty.', max_length=300, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical faculty',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalDepartment',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the department.', max_length=300, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('faculty', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='agreements.Faculty')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical department',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalAgreement',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=300)),
                ('slug', models.SlugField(help_text='URL-safe identifier for the agreement.', max_length=300, validators=[django.core.validators.RegexValidator(inverse_match=True, message="The slug cannot be 'create'.", regex='^create$')])),
                ('created', models.DateField(blank=True, editable=False)),
                ('start', models.DateTimeField(default=django.utils.timezone.now, help_text='The agreement is valid starting at this date and time. Format (UTC timezone): YYYY-MM-DD HH:MM:SS')),
                ('end', models.DateTimeField(blank=True, default=agreements.models.date_121_days_from_now, help_text='The agreement is valid until this date and time. Format (UTC timezone): YYYY-MM-DD HH:MM:SS', null=True)),
                ('body', django_bleach.models.BleachField(help_text='HTML content of the agreement. The following tags are allowed: h3, p, a, abbr, cite, code, small, em, strong, sub, sup, u, ul, ol, li. Changing this field after the agreement has been signed by patrons is strongly discouraged.')),
                ('redirect_url', models.URLField(help_text="URL where patrons will be redirected to after signing the agreement. It must start with 'https://'.", validators=[django.core.validators.URLValidator(code='need_https', message="Enter a valid URL. It must start with 'https://'.", schemes=['https'])])),
                ('redirect_text', models.CharField(help_text='The text of the URL redirect link.', max_length=300)),
                ('hidden', models.BooleanField(default=False, help_text='Hidden agreements do not appear in the list of active agreements.')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='agreements.Resource')),
            ],
            options={
                'verbose_name': 'historical agreement',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
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
            constraint=models.UniqueConstraint(fields=('agreement', 'signatory'), name='agreements_signature_unique_signature'),
        ),
        migrations.AddConstraint(
            model_name='licensecode',
            constraint=models.UniqueConstraint(fields=('resource', 'code'), name='agreements_licensecode_unique_codes_per_resource'),
        ),
        migrations.AddConstraint(
            model_name='agreement',
            constraint=models.CheckConstraint(check=models.Q(('end__isnull', True), ('end__gt', django.db.models.expressions.F('start')), _connector='OR'), name='agreements_agreement_end_null_or_gt_start'),
        ),
    ]
