# Generated by Django 5.1 on 2024-09-12 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PanelModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=255)),
                ('airbag_icon', models.JSONField(blank=True, null=True)),
                ('labels', models.JSONField(blank=True, null=True)),
                ('image_airbag_icon_origin', models.ImageField(blank=True, max_length=255, null=True, upload_to='images/panel/complete')),
                ('image_airbag_icon', models.ImageField(blank=True, max_length=255, null=True, upload_to='images/panel/reconhecidas_airbag')),
                ('runtime', models.FloatField(default=0.0)),
            ],
        ),
    ]
