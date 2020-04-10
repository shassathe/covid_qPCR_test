# Generated by Django 2.1.1 on 2020-04-10 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qpcr_records', '0008_test_results_sample_bag_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='test_results',
            name='peter_rwp_id',
        ),
        migrations.AddField(
            model_name='test_results',
            name='qsp_id',
            field=models.CharField(default='', help_text='Scan or Enter Barcode of qPCR_Storage Plate', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qsp_well',
            field=models.CharField(default='', max_length=3),
        ),
    ]
