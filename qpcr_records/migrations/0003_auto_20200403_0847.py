# Generated by Django 3.0.3 on 2020-04-03 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qpcr_records', '0002_auto_20200403_0738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test_results',
            name='qpcr_n1_well',
            field=models.CharField(default='X', max_length=5),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='qpcr_n2_well',
            field=models.CharField(default='X', max_length=5),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='qpcr_rp_well',
            field=models.CharField(default='X', max_length=5),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='sampling_plate_well',
            field=models.CharField(default='X', max_length=5),
        ),
    ]
