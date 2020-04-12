# Generated by Django 3.0.3 on 2020-04-08 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qpcr_records', '0005_auto_20200406_0208'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='test_results',
            name='qpcr_record_barcode_b3f268_idx',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='institute',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='lab',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='ms2_ct_mean_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='ms2_ct_sd_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='n_ct_mean_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='n_ct_sd_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='orf1ab_ct_mean_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='orf1ab_ct_sd_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_1_id',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_1_well',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_2_id',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_2_well',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_3_id',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_3_well',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_4_id',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_4_well',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_5_id',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_5_well',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_6_id',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='plate_6_well',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='rna_extraction_protocol',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='s_ct_mean_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='s_ct_sd_value',
        ),
        migrations.RemoveField(
            model_name='test_results',
            name='technician',
        ),
        migrations.AddField(
            model_name='test_results',
            name='decision_tree_results',
            field=models.CharField(choices=[('Undetermined', 'Undetermined'), ('Invalid', 'Invalid'), ('Inconclusive', 'Inconclusive'), ('Positive', 'Positive'), ('Negative', 'Negative')], default='Undetermined', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='eds_results_csv',
            field=models.URLField(default='', max_length=300),
        ),
        migrations.AddField(
            model_name='test_results',
            name='enzyme_mix_id',
            field=models.CharField(default='', help_text='Enter qRTPCR Reaction Enzyme Mix Lot Number', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='epm_id',
            field=models.CharField(default='', help_text='Enter EpMotion ID', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='file_transfer_status',
            field=models.CharField(choices=[('Complete', 'Complete'), ('Not Complete', 'Not Complete')], default='Not Complete', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='final_results',
            field=models.CharField(choices=[('Undetermined', 'Undetermined'), ('Invalid', 'Invalid'), ('Inconclusive', 'Inconclusive'), ('Positive', 'Positive'), ('Negative', 'Negative')], default='Undetermined', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='frz_id',
            field=models.CharField(default='', help_text='Enter RNA Storage Freezer Number', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='kfr_id',
            field=models.CharField(default='', help_text='Enter KingFisher Number', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='mhv_id',
            field=models.CharField(default='', help_text='Enter Mosquito HV Number', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='ms2_lot_id',
            field=models.CharField(default='', help_text='Enter MS2 Control Lot #', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='probe_mix_id',
            field=models.CharField(default='', help_text='Enter qRTPCR Reaction Probe Mix Lot Number', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qpcr_technician',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qpcr_technician_institute',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qpcr_technician_lab',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qrp_id',
            field=models.CharField(default='', help_text='Scan or Enter Barcode of qRTPCR Reaction Plate', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qrp_well',
            field=models.CharField(default='', max_length=3),
        ),
        migrations.AddField(
            model_name='test_results',
            name='qs5_id',
            field=models.CharField(default='', help_text='Enter QS5 Number', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rep_id',
            field=models.CharField(default='', help_text='Scan or Enter Barcode of RNA Elution Plate', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rep_well',
            field=models.CharField(default='', max_length=3),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rna_extract_reagent_ids',
            field=models.CharField(default='', help_text='Enter list of RNA extraction reagent IDs', max_length=200),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rna_extraction_technician',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rna_extraction_technician_institute',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rna_extraction_technician_lab',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rsp_id',
            field=models.CharField(default='', help_text='Scan or Enter Barcode of RNA Storage Plate', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rsp_well',
            field=models.CharField(default='', max_length=2),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rwp_id',
            field=models.CharField(default='', help_text='Scan or Enter Barcode of RNA Working Plate', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='rwp_well',
            field=models.CharField(default='', max_length=3),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_extraction_technician1',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_extraction_technician1_institute',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_extraction_technician1_lab',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_extraction_technician2',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_extraction_technician2_institute',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_extraction_technician2_lab',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sample_release',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No'), ('NA', 'NA')], default='NA', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sep_id',
            field=models.CharField(default='', help_text='Scan or Enter Barcode of Sample Extraction Plate (SEP)', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='sep_well',
            field=models.CharField(default='', max_length=3),
        ),
        migrations.AddField(
            model_name='test_results',
            name='ssp_id',
            field=models.CharField(default='', help_text='Sample Storage Plate (SSP)', max_length=15),
        ),
        migrations.AddField(
            model_name='test_results',
            name='ssp_well',
            field=models.CharField(default='', max_length=3),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='barcode',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='fake_name',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='ms2_ct_value',
            field=models.FloatField(default=-1),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='n_ct_value',
            field=models.FloatField(default=-1),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='orf1ab_ct_value',
            field=models.FloatField(default=-1),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='pcr_results_csv',
            field=models.URLField(default='', max_length=300),
        ),
        migrations.AlterField(
            model_name='test_results',
            name='s_ct_value',
            field=models.FloatField(default=-1),
        ),
        migrations.AddIndex(
            model_name='test_results',
            index=models.Index(fields=['barcode', 'ssp_id', 'sep_id', 'rep_id', 'rsp_id', 'rwp_id', 'qrp_id'], name='qpcr_record_barcode_858126_idx'),
        ),
    ]