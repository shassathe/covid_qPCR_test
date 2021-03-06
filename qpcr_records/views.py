# django imports
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from django.forms import model_to_dict
from django.contrib import messages
from django.utils.safestring import mark_safe

# models, tables and forms import
from qpcr_records.models import *
from qpcr_records.forms import *
from qpcr_records.data_processing.results import Results

# miscellaneous imports
from decouple import config
from datetime import date, timedelta, datetime
import boto3
from math import pi
import pandas as pd

# plotting
from bokeh.plotting import figure
from bokeh.models import LinearAxis, ColumnDataSource
from bokeh.models.tools import HoverTool, PanTool
from bokeh.embed import components
from bokeh.models import Range1d
from bokeh.models.tickers import AdaptiveTicker
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
from bokeh.layouts import row

"""
@login_required implements a check by django for login credentials. Add this tag to every function to enforce checks for
 user logins. If the check returns False, user will be automatically redirected to the login page
 Functions/views without this tag will be publicly accessible
"""


def reset_session(request):
    """
    Deletes all session variables. Authentication variables are not reset.
    This functions will be called each time a user user lands on the home / index view
    """
    for k in list(request.session.keys()):
        if k not in ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']:
            del request.session[k]


def dashboard(request):
    """
    Generate summaries for the dashboard. Called each time a user lands on the dahboard page
    """
    summary_data = get_dashboard_data()
    print(summary_data.keys())
    return render(request, 'qpcr_records/dashboard.html', {'summary_data': summary_data})


def get_dashboard_data():
    """
    Performs queries to show sample information for the overall dashboard public view
    """
    rchsd = pd.read_csv('qpcr_records/aggregates/data-aggr_sngl_spec_pr_sub-20200624-rchsd.csv')
    scripps = pd.read_csv('qpcr_records/aggregates/data-aggr_sngl_spec_pr_sub-20200624-scripps.csv')
    symptoms = pd.read_csv('qpcr_records/aggregates/data-pos_symptom_count-20200624.csv')

    pos_symptoms = dict()
    neg_symptoms = dict()
    for i, j in zip(['symp_chills_yn', 'symp_cough_yn', 'symp_diarrhea_yn', 'symp_fatigue_yn', 'symp_fever_yn',
                     'symp_myalgia_yn', 'symp_nausea_yn', 'symp_rash_yn', 'symp_runny_nose_yn', 'symp_sob_yn',
                     'symp_sore_throat_yn', 'symp_stuffy_nose_yn', 'symp_trbl_breathing_yn', 'symp_vomit_yn'],
                    ['Chills', 'Cough', 'Diarrhea', 'Fatigue', 'Fever', 'Myalgia', 'Nausea', 'Rash', 'Runny Nose',
                     'Sob', 'Sore Throat', 'Stuffy Nose', 'Trouble Breathing', 'Vomiting']):
        neg_symptoms[j] = rchsd[i] + scripps[i + '_scrp'] - symptoms[i]
        pos_symptoms[j] = symptoms[i]
    # ['plots_script', 'main_plot', 'overall_num_tot_cases', 'overall_num_pos_cases', 'overall_num_neg_cases',
    # 'overall_pct_pos_cases', 'overall_pct_neg_cases', 'todays_date', 'today_num_tot_cases', 'today_num_pos_cases',
    # 'today_num_neg_cases', 'today_pct_pos_cases', 'today_pct_neg_cases']

    # Gather the results of all the cases we've extracted so far along with when they were sampled
    script1, div1, script2, div2 = plot_trend_chart(pos_symptoms, neg_symptoms)

    dashboard_information = {
        'trend_plot_script': script1,
        'trend_plot_div': div1,
        'symptom_script': script2,
        'symptom_div': div2,
        # All of the overall testing numbers to include in the dashboard
        'overall_num_tot_cases': rchsd.loc[0, 'subj_count'] + scripps.loc[0, 'subj_count'],
        'overall_num_pos_cases': rchsd.loc[0, 'pos_count'] + scripps.loc[0, 'pos_count'],
        'overall_num_neg_cases': rchsd.loc[0, 'neg_count'] + scripps.loc[0, 'neg_count'],
        'overall_pct_pos_cases': round((rchsd.loc[0, 'pos_count'] + scripps.loc[0, 'pos_count']) /
                                       (rchsd.loc[0, 'subj_count'] + scripps.loc[0, 'subj_count']) * 100, 4),
        'overall_pct_neg_cases': round((rchsd.loc[0, 'neg_count'] + scripps.loc[0, 'neg_count']) /
                                       (rchsd.loc[0, 'subj_count'] + scripps.loc[0, 'subj_count']) * 100, 4),
        # Numbers by Testing Sites
        'rchsd_num_tot_cases': rchsd.loc[0, 'subj_count'],
        'rchsd_num_pos_cases': rchsd.loc[0, 'pos_count'],
        'rchsd_pct_pos_cases': round(rchsd.loc[0, 'pos_count'] / rchsd.loc[0, 'subj_count'] * 100, 4),
        'rchsd_num_neg_cases': rchsd.loc[0, 'neg_count'],
        'rchsd_pct_neg_cases': round(rchsd.loc[0, 'neg_count'] / rchsd.loc[0, 'subj_count'] * 100, 4),

        'scripps_num_tot_cases': scripps.loc[0, 'subj_count'],
        'scripps_num_pos_cases': scripps.loc[0, 'pos_count'],
        'scripps_pct_pos_cases': round(scripps.loc[0, 'pos_count'] / scripps.loc[0, 'subj_count'] * 100, 4),
        'scripps_num_neg_cases': scripps.loc[0, 'neg_count'],
        'scripps_pct_neg_cases': round(scripps.loc[0, 'neg_count'] / scripps.loc[0, 'subj_count'] * 100, 4),
    }
    return dashboard_information


def plot_trend_chart(p_symptoms, n_symptoms):
    """
    Generate bar and line plots to summarize data. Returns the javascript that can be embedded in web page to display
    the plots
    :param cases: django queryset
    :return componenets(p): embedable javascript for plot 'p'
    """
    # CASE TREND PLOT
    obj = test_results.objects.filter(project='Radys')
    obj = obj.exclude(barcode__contains='.')
    result_summary = pd.DataFrame(
        obj.exclude(barcode__contains='-').values_list('sampling_date', 'final_results', 'project'))

    # Reformat data for bokeh plotting
    result_summary.columns = ['sampling_date', 'final_results', 'project']
    result_summary = result_summary[result_summary['project'] == 'Radys']
    result_summary = result_summary.groupby('sampling_date').apply(lambda r: r['final_results'].value_counts())

    # If you only have a single entry in the database, you don't need to reset the index and pivot
    if result_summary.shape[0] > 1:
        result_summary = result_summary.reset_index().pivot(index='sampling_date', columns='level_1',
                                                            values='final_results')
    result_summary = result_summary[['Negative', 'Positive']]
    result_summary.fillna(0, inplace=True)

    result_summary.index = result_summary.index.astype('datetime64[ns]')
    result_summary[['Positive', 'Negative']] = result_summary[['Positive', 'Negative']].astype(int)
    result_summary['Positive_Rolling_Mean'] = result_summary['Positive'].rolling(5).mean()
    result_summary['Positive_Rolling_Mean'] = result_summary['Positive_Rolling_Mean'].fillna(0)

    source = ColumnDataSource(data=result_summary.reset_index())
    p1 = figure(plot_height=500, x_axis_type='datetime', tools=[PanTool(dimensions='width')])
    p1.varea_stack(['Negative'], x='sampling_date', color=("forestgreen"), alpha=0.7, source=source,
                   legend=['# of samples tested'])
    y_range = Range1d(0, result_summary['Negative'].max() + 5)
    hover_tool = HoverTool(tooltips=[("Date", "@sampling_date{%F}"), ("Positive", "@Positive"),
                                     ("Negative", "@Negative")], formatters={"@sampling_date": "datetime"})
    p1.add_tools(hover_tool)

    p1.yaxis.axis_label = "Samples Tested Per Day"
    p1.yaxis.ticker = AdaptiveTicker(min_interval=1)

    p1.extra_y_ranges = {"Positive_Rolling_Mean": Range1d(start=0, end=result_summary['Positive_Rolling_Mean'].max())}
    p1.line(x='sampling_date', y='Positive_Rolling_Mean', source=result_summary, color='firebrick', line_width=3,
            y_range_name='Positive_Rolling_Mean', legend='5 day mean positive samples')
    p1.add_layout(LinearAxis(y_range_name="Positive_Rolling_Mean", axis_label="5 Day Rolling Mean of Positive Cases"),
                  'right')
    # Style plot
    p1.toolbar_location = "above"
    p1.sizing_mode = 'stretch_both'
    p1.outline_line_color = None
    p1.toolbar.logo = None
    p1.toolbar.autohide = False
    p1.ygrid.grid_line_color = None

    p1.legend.location = "top_left"
    p1.legend.title = "Case Status"
    p1.legend.title_text_font_style = "bold"
    p1.legend.title_text_font_size = "20px"

    p1.xaxis.axis_label = "Date"
    p1.xaxis.axis_label_text_font_size = "18px"
    p1.xaxis.major_label_text_font_size = "16px"

    p1.yaxis.axis_label_text_font_size = "18px"
    p1.yaxis[0].axis_label_text_color = "forestgreen"
    p1.yaxis[1].axis_label_text_color = "firebrick"
    p1.yaxis.major_label_text_font_size = "16px"
    p1.yaxis.minor_tick_line_color = None

    # PIE CHART
    data = pd.DataFrame.from_dict(p_symptoms, orient='index')
    data = data.reset_index()
    data.columns = ['Symptoms', 'Count']
    data['angle'] = data['Count'] / data['Count'].sum() * 2 * pi
    data['color'] = Category20c[len(p_symptoms)]
    data = data.sort_values('Count', ascending=False)
    l = list(data['Symptoms'])

    p2 = figure(plot_height=400, title='Positive Subjects', toolbar_location=None, tools="hover",
                tooltips="@Symptoms: @Count", x_range=(-0.5, 1.0))
    p2.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
             line_color="white", fill_color='color', legend_field='Symptoms', source=data)
    p2.axis.axis_label = None
    p2.axis.visible = False
    p2.grid.grid_line_color = None
    p2.toolbar.autohide = True
    p2.grid.visible = False
    p2.outline_line_color = None
    p2.title.align = "left"

    data = pd.DataFrame.from_dict(n_symptoms, orient='index')
    data = data.reset_index()
    data.columns = ['Symptoms', 'Count']
    data['angle'] = data['Count'] / data['Count'].sum() * 2 * pi
    data['color'] = Category20c[len(n_symptoms)]
    data = data.sort_values('Count', ascending=False)
    data = data.set_index('Symptoms').loc[l].reset_index()

    p3 = figure(plot_height=400, title='Negative Subjects', toolbar_location=None, tools="hover",
                tooltips="@Symptoms: @Count", x_range=(-0.5, 1.0))
    p3.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
             line_color="white", fill_color='color', legend_field='Symptoms', source=data)
    p3.axis.axis_label = None
    p3.axis.visible = False
    p3.grid.grid_line_color = None
    p3.toolbar.autohide = True
    p3.legend.visible = False
    p3.grid.visible = False
    p3.outline_line_color = None
    p3.title.align = "left"

    s1, d1 = components(p1)
    p4 = row(p2, p3)
    p4.sizing_mode = 'stretch_both'
    s2, d2 = components(p4)
    return s1, d1, s2, d2


def sample_counter_display():
    """
    Performs queries to determine the number of unprocessed samples, sample extraction plates,
    RNA extraction plates, RNA working plates, running qPCR plates, qPCR plates with results,
    processed qPCR plates, and cleared results. Returns a dictionary with these values.

    We are calculating the plates from each stage backwards by subtracting the number of plates in the current stage
    being evaluated timestamp threshold of 48 hours
    """
    time_thresh = date.today() - timedelta(days=2)

    # Cleared plate counter
    data_cleared = test_results.objects.filter(~Q(final_results=''),
                                               sampling_date__gte=time_thresh).count()

    # qPCR plate counters
    q_processed = test_results.objects.filter(~Q(decision_tree_results='Undetermined'),
                                              sampling_date__gte=time_thresh, final_results='').count()

    q_recorded = test_results.objects.filter(~Q(qpcr_results_file=''), sampling_date__gte=time_thresh,
                                             decision_tree_results='Undetermined').count()

    q_running = test_results.objects.filter(~Q(qrp_id=''), sampling_date__gte=time_thresh, qpcr_results_file='').count()
    s = list(set(test_results.objects.filter(~Q(qrp_id=''), sampling_date__gte=time_thresh).values_list(
        'qrp_id', flat=True).order_by('qrp_id')))
    qrp_id = ', '.join(s)
    qrp_plate = len(s)

    # RNA plate counters
    rwp_count = test_results.objects.filter(~Q(rwp_id=''),
                                            sampling_date__gte=time_thresh, qrp_id='').count()  # rna working plate
    s = list(set(
        test_results.objects.filter(~Q(rwp_id=''), sampling_date__gte=time_thresh).values_list('rwp_id', flat=True)))
    rwp_id = ', '.join(s)
    rwp_count_plate = len(list(set(
        test_results.objects.filter(~Q(rwp_id=''), sampling_date__gte=time_thresh, qrp_id='').values_list('rwp_id',
                                                                                                          flat=True))))
    rwp_id = ', '.join(s)

    rep_count = test_results.objects.filter(~Q(rep_id=''),
                                            sampling_date__gte=time_thresh, rwp_id='').count()  # rna extraction plate
    s = list(set(
        test_results.objects.filter(~Q(rep_id=''), sampling_date__gte=time_thresh).values_list('rep_id', flat=True)))
    rep_id = ', '.join(s)
    rep_count_plate = len(list(set(
        test_results.objects.filter(~Q(rep_id=''), sampling_date__gte=time_thresh, rwp_id='').values_list('rep_id',
                                                                                                          flat=True))))

    # Sample extraction plate counter
    sep_count = test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh, rep_id='').count()
    s = list(set(
        test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh).values_list('sep_id', flat=True)))
    sep_id = ', '.join(s)
    sep_count_plate = len(list(set(
        test_results.objects.filter(~Q(sep_id=''), sampling_date__gte=time_thresh, rep_id='').values_list('sep_id',
                                                                                                          flat=True))))

    # Unprocessed sample counter
    unproc_samples = test_results.objects.filter(~Q(barcode=''), sampling_date__gte=time_thresh, sep_id='').count()

    # General results tabulation
    final_results = list(test_results.objects.values_list('final_results', flat=True))
    num_positives, num_negatives, num_undetermined = 0, 0, 0
    for result in final_results:
        if result == 'Positive':
            num_positives += 1
        elif result == 'Negative':
            num_negatives += 1
        elif result == 'Undetermined':
            num_undetermined += 1

    # Compile all of the results into a dictionary to return to webpages via Django
    counter_information = {
        'unproc_samples': unproc_samples,
        'sep_count': sep_count, 'sep_count_plate': sep_count_plate, 'sep_ids': sep_id,
        'rep_count': rep_count, 'rep_count_plate': rep_count_plate, 'rep_ids': rep_id,
        'rwp_count': rwp_count, 'rwp_count_plate': rwp_count_plate, 'rwp_ids': rwp_id,
        'q_running': q_running, 'q_running_plate': qrp_plate, 'q_running_ids': qrp_id,
        'q_recorded': q_recorded,
        'q_processed': q_processed,
        'data_cleared': data_cleared,
        'num_samples': len(final_results),  # total number of samples present
        'num_positives': num_positives, 'num_negatives': num_negatives, 'num_undetermined': num_undetermined,
        'p_positive': round(num_positives / len(final_results) * 100, 2) if len(final_results) > 0 else 0,
        'p_negative': round(num_negatives / len(final_results) * 100, 2) if len(final_results) > 0 else 0,
        'p_undetermined': round(num_undetermined / len(final_results) * 100, 2) if len(final_results) > 0 else 0,
    }
    return counter_information


@login_required
def index(request):
    """
    Login page redirects here
    """

    # Sample Counter Display - Will appear every time the home page is loaded
    counter_information = sample_counter_display()

    # RESET ALL SESSION DATA EXCEPT FOR USER LOGIN
    reset_session(request)
    return render(request, 'qpcr_records/index.html', counter_information)


@login_required
def platemap_upload(request):
    # Show initial form
    if request.method == 'GET':
        f = PlatemapUploadForm()
        return render(request, 'qpcr_records/platemap_upload.html', {'form': f})
    # Upon form submission, redirect to index if valid
    else:
        f = PlatemapUploadForm(request.POST, request.FILES)

        if f.is_valid():
            platemap = pd.read_csv(request.FILES['platemap_file'], index_col=0, names=['barcode'])
            platemap = platemap.dropna()

            # Write barcodes to db
            objs = list()
            for i in platemap.index:
                if i in ['A1', 'H1']:
                    continue
                else:
                    entry = test_results(barcode=platemap.loc[i, 'barcode'], ssp_id=f.cleaned_data['ssp_id'],
                                         ssp_well=i,
                                         sep_id=f.cleaned_data['sep_id'], sep_well=i, rep_well=i, rsp_well=i,
                                         sampling_date=date.today().strftime('%Y-%m-%d'),
                                         sampling_time=datetime.now().strftime("%H:%M:%S"),
                                         personnel1_andersen_lab=request.user.get_full_name(),
                                         personnel2_andersen_lab=f.cleaned_data['personnel2_andersen_lab'].strip(),
                                         sample_bag_id=f.cleaned_data['sample_bag_id'])
                    objs.append(entry)
            test_results.objects.bulk_create(objs)

            backup_filename = f.cleaned_data["sep_id"] + '_' + str(date.today().strftime("%y-%m-%d")) + '.csv'
            df = pd.DataFrame([model_to_dict(entry) for entry in objs])
            s3 = boto3.resource('s3', region_name=config('aws_s3_region_name'),
                                aws_access_key_id=config('aws_access_key_id'),
                                aws_secret_access_key=config('aws_secret_access_key'))
            s3.Bucket(config('aws_storage_bucket_name')).put_object(Key=backup_filename, Body=df.to_csv())
            s3_filepath = config('aws_bucket_link') + backup_filename
            objs = test_results.objects.filter(sep_id=f.cleaned_data['sep_id']).update(sampling_plate_csv=s3_filepath)

            messages.success(request, mark_safe('Barcodes list uploaded successfully.'))
            return redirect('index')
        else:  # Show form again with user data and errors
            return render(request, 'qpcr_records/platemap_upload.html', {'form': f})


@login_required
def perform_safety_check(request):
    """
    Present list of safety checks to user before starting plating.
    :param request: signal call that this function has been called
    """
    # Show initial form
    if request.method == 'GET':
        f = LysisReagentLotForm(initial={'lrl_id': 'M6246109105'})
        return render(request, 'qpcr_records/perform_safety_check.html', {'form': f})
    # Upon form submission, redirect to barcode_capture if valid
    else:
        f = LysisReagentLotForm(request.POST)
        if f.is_valid():
            request.session['lrl_id'] = f.cleaned_data['lrl_id']
            request.session['personnel2_andersen_lab'] = f.cleaned_data['personnel2_andersen_lab']
            return redirect('barcode_capture')
        else:
            return render(request, 'qpcr_records/perform_safety_check.html', {'form': f})


@login_required
def barcode_capture(request):
    """
    Redirected here after the plate barcode has been scanned. User will be prompted to scan a barcode until the second
    to last well is scanned. After scanning the last well, database records for each barcode will be created and the
    user will be routed to a success page.
    :param request: signal call that this function has been called
    :return f: captured barcode
    """
    d1 = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E',
          'E': 'F', 'F': 'G', 'G': 'H', 'H': 'A'}

    for k in request.GET.keys():
        request.session[k] = request.GET[k]

    # Initial visit via redirect
    if request.method == 'GET':
        start_well = 'A1'
        request.session['barcodes'] = dict()
        f = SampleStorageAndExtractionWellForm(initial={'ssp_well': start_well, 'sep_well': start_well})
        return render(request, 'qpcr_records/barcode_capture.html',
                      {'form': f, 'barcodes': request.session['barcodes']})
    # Progressing through wells
    else:
        f = SampleStorageAndExtractionWellForm(request.POST)

        # Proceed to next well accordingly
        if f.is_valid():
            # Save well barcodes to session
            active_well = f.cleaned_data['sep_well']
            request.session[active_well] = f.cleaned_data['barcode']
            request.session['barcodes'][active_well] = f.cleaned_data['barcode']
            barcodes = request.session['barcodes']

            # Last well reached; redirect to plate form
            if active_well == 'H12':
                return redirect('sample_plate_capture')
            # Next well
            else:
                if active_well == 'G1':
                    well = 'A2'
                else:
                    row = active_well[0]
                    col = int(active_well[1:])
                    if row == 'H':
                        row = d1[row]
                        col = col + 1
                    else:
                        row = d1[row]

                    well = row + str(col)
                f = SampleStorageAndExtractionWellForm(initial={'sep_well': well, 'ssp_well': well})
                return render(request, 'qpcr_records/barcode_capture.html', {'form': f, 'barcodes': barcodes})
        else:  # Initial submission of control wells
            # Initialize variables
            first_sample_well = 'B1'
            f = SampleStorageAndExtractionWellForm(
                initial={'sep_well': first_sample_well, 'ssp_well': first_sample_well})
            return render(request, 'qpcr_records/barcode_capture.html',
                          {'form': f, 'barcodes': request.session['barcodes']})


@login_required
def update_existing_records(request):
    """
    Index page for updating existing records
    :param request:
    :return:
    """
    reset_session(request)
    # Sample Counter Display - Will appear every time the home page is loaded
    counter_information = sample_counter_display()
    return render(request, 'qpcr_records/update_existing_records.html', counter_information)


@login_required
def sample_plate_capture(request):
    # Render initial form
    if request.method == 'GET':
        f = SampleStorageAndExtractionPlateForm()
        return render(request, 'qpcr_records/sample_plate_capture.html',
                      {'form': f, 'barcodes': request.session['barcodes']})
    else:  # Upon form submission, redirect according to validation
        f = SampleStorageAndExtractionPlateForm(request.POST)
        # Save barcodes to db
        if f.is_valid():
            l = list()
            for i in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                for j in range(1, 13):
                    well = i + str(j)
                    if well in ['A1', 'H1']:
                        continue
                    elif well not in request.session.keys():
                        continue
                    else:
                        entry = test_results(barcode=request.session[well].strip(),
                                             ssp_id=f.cleaned_data['ssp_id'],
                                             ssp_well=well,
                                             sep_id=f.cleaned_data['sep_id'],
                                             sep_well=well,
                                             rep_well=well,
                                             rsp_well=well,
                                             sampling_date=date.today().strftime('%Y-%m-%d'),
                                             sampling_time=datetime.now().strftime("%H:%M:%S"),
                                             lrl_id=request.session['lrl_id'].strip(),
                                             personnel1_andersen_lab=request.user.get_full_name(),
                                             personnel2_andersen_lab=request.session['personnel2_andersen_lab'].strip(),
                                             sample_bag_id=f.cleaned_data['sample_bag_id'])
                        l.append(entry)

            test_results.objects.bulk_create(l)

            # Backup results to file and upload to S3 bucket

            backup_filename = f.cleaned_data["sep_id"] + '_' + str(date.today().strftime("%y-%m-%d")) + '.csv'
            df = pd.DataFrame([model_to_dict(entry) for entry in l])
            s3 = boto3.resource('s3', region_name=config('aws_s3_region_name'),
                                aws_access_key_id=config('aws_access_key_id'),
                                aws_secret_access_key=config('aws_secret_access_key'))
            s3.Bucket(config('aws_storage_bucket_name')).put_object(Key=backup_filename, Body=df.to_csv())
            s3_filepath = config('aws_bucket_link') + backup_filename
            objs = test_results.objects.filter(sep_id=f.cleaned_data['sep_id']).update(sampling_plate_csv=s3_filepath)

            messages.success(request, mark_safe(f'{len(l)} samples added successfully.'))
            return redirect('index')
        # Invalid form
        else:
            return render(request, 'qpcr_records/sample_plate_capture.html',
                          {'form': f, 'barcodes': request.session['barcodes']})


@login_required
def rna_plate_capture(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    # Render initial form
    if request.method == 'GET':
        f = RNAExtractionPlateForm(initial={'ms2_lot_id': '2003001'})
        return render(request, 'qpcr_records/rna_plate_capture.html', {'form': f})
    else:  # Upon form submission, redirect according to validation
        f = RNAExtractionPlateForm(request.POST)

        if f.is_valid():
            objs = test_results.objects.filter(sep_id=f.cleaned_data['sep_id']).update(
                rep_id=f.cleaned_data['rep_id'].strip(),
                re_date=date.today().strftime('%Y-%m-%d'),
                rsp_id=f.cleaned_data['rep_id'].strip(),
                ms2_lot_id=f.cleaned_data['ms2_lot_id'].strip(),
                personnel_knight_lab=request.user.get_full_name(),
                kfr_id=f.cleaned_data['kfr_id'].strip(),
                rna_extract_kit_id=f.cleaned_data['rna_extract_kit_id'],
                megabeads_id=f.cleaned_data['megabeads_id'],
                rna_extraction_time=datetime.now().strftime("%H:%M:%S"),
                carrier_rna_id=f.cleaned_data['carrier_rna_id'])

            # Redirect to homepage
            messages.success(request, mark_safe('RNA plates added successfully.'))
            return redirect('index')
        # Invalid form
        else:
            return render(request, 'qpcr_records/rna_plate_capture.html', {'form': f})


@login_required
def rwp_plate_capture(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    if request.method == 'GET':
        f = ArrayingForm()
        return render(request, 'qpcr_records/rwp_plate_capture.html', {'form': f})
    else:  # Upon form submission, redirect according to validation
        f = ArrayingForm(request.POST)

        # Array form
        if f.is_valid():
            objs = test_results.objects.filter(rep_id__in=[f.cleaned_data['barcode1'], f.cleaned_data['barcode2'],
                                                           f.cleaned_data['barcode3'],
                                                           f.cleaned_data['barcode4']]).update(
                rwp_id=f.cleaned_data['rwp_id'],
                epm_id=f.cleaned_data['epm_id'])

            # CONVERT 4X96-WELL PLATE LAYOUT TO 1X384-WELL PLATE LAYOUT
            d = dict()
            rows_384 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
            cols_384 = range(1, 25)
            col_index = 0
            row_index = 0
            for z in range(0, 4):
                for col1, col2 in zip([1, 3, 5, 7, 9, 11], [2, 4, 6, 8, 10, 12]):
                    for row in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                        d[str(z) + row + str(col1)] = rows_384[row_index] + \
                                                      str(cols_384[col_index])
                        row_index = row_index + 1
                        d[str(z) + row + str(col2)] = rows_384[row_index] + \
                                                      str(cols_384[col_index])
                        row_index = row_index + 1

                    col_index = col_index + 1
                    row_index = 0

            barcode_list = list()
            i = 0
            for b in [f.cleaned_data['barcode1'], f.cleaned_data['barcode2'],
                      f.cleaned_data['barcode3'], f.cleaned_data['barcode4']]:
                if b in barcode_list:
                    continue
                else:
                    for z in test_results.objects.filter(rep_id=b).values_list('sep_well', flat=True):
                        test_results.objects.filter(rep_id=b, sep_well=z).update(rwp_well=d[str(i) + z],
                                                                                 rsp_well=d[str(i) + z],
                                                                                 arraying_time=datetime.now().strftime(
                                                                                     "%H:%M:%S"),
                                                                                 qrp_well=d[str(i) + z])
                    i = i + 1

                barcode_list.append(b)
            messages.success(request, mark_safe('RNA working plate added successfully.'))
            return redirect('index')
        else:  # Invalid form
            return render(request, 'qpcr_records/rwp_plate_capture.html', {'form': f})


@login_required
def qpcr_plate_capture(request):
    """
    Redirected here after the barcode for the last well is scanned. Create a platemap for display with the barcodes
    specified along the corresponding well.
    Also, records for each barcode will be created.
    :param request:
    :return:
    """
    if request.method == 'GET':
        f = QPCRStorageAndReactionPlateForm()
        return render(request, 'qpcr_records/qpcr_plate_capture.html', {'form': f})
    else:
        f = QPCRStorageAndReactionPlateForm(request.POST)

        if f.is_valid():
            objs = test_results.objects.filter(rwp_id=f.cleaned_data['rwp_id']).update(
                qrp_id=f.cleaned_data['qrp_id'],
                qpcr_date=date.today().strftime('%Y-%m-%d'),
                qpcr_reaction_time=datetime.now().strftime("%H:%M:%S"),
                personnel_laurent_lab=request.user.get_full_name())

            messages.success(request, mark_safe('qRT-PCR plate added successfully.'))
            return redirect('index')
        else:
            return render(request, 'qpcr_records/qpcr_plate_capture.html', {'form': f})


@login_required
def search(request):
    """
    Pass the search form to the django template. User has to fill at least one field for a successful search
    :param request:
    :param request: signal call that this function has been called
    :return f: form to display to search forms
    """
    # Show initial form
    if request.method == 'GET':
        f = SearchForm()
        return render(request, 'qpcr_records/search.html', {'form': f})
    # Upon form submission, redirect to search_results if valid
    else:
        f = SearchForm(request.POST)
        if f.is_valid():
            request.session['search'] = dict()
            for field, value in f.cleaned_data.items():
                request.session['search'][field] = value
            return redirect('search_results')
        else:
            # Show form again with errors
            return render(request, 'qpcr_records/search.html', {'form': f})


@login_required
def search_results(request):
    """
    Function to search records based on the fields. User has to enter at least one field to complete a successful search
    :param request: GET request with search parameters
    :return table: Returns a django-tables2 object to be displayed on the webpage
    """
    if request.method == 'GET':
        # ['csrfmiddlewaretoken', 'barcode', 'sampling_date', 'plate_id', 'technician', 'result', 'sample_bag_id']

        q = ''
        for field, value in request.session['search'].items():
            if value == "" or value == 'None':
                continue
            else:
                if field == 'barcode':
                    if q == '':
                        q = test_results.objects.filter(barcode__iexact=value)
                    else:
                        q = q.filter(barcode__iexact=value)
                elif field == 'sampling_date':
                    if q == '':
                        q = test_results.objects.filter(sampling_date__iexact=value)
                    else:
                        q = q.filter(sampling_date__iexact=value)
                elif field == 'plate_id':
                    if q == '':
                        q = test_results.objects.filter(Q(ssp_id__iexact=value.strip()) |
                                                        Q(sep_id__iexact=value.strip()) |
                                                        Q(rep_id__iexact=value.strip()) |
                                                        Q(rwp_id__iexact=value.strip()) |
                                                        Q(rsp_id__iexact=value.strip()) |
                                                        Q(qrp_id__iexact=value.strip()))
                    else:
                        q = q.filter(
                            Q(ssp_id__iexact=value.strip()) | Q(sep_id__iexact=value.strip()) |
                            Q(rep_id__iexact=value.strip()) | Q(rwp_id__iexact=value.strip()) |
                            Q(rsp_id__iexact=value.strip()) | Q(qrp_id__iexact=value.strip()))
                elif field == 'technician':
                    if q == '':
                        q = test_results.objects.filter(Q(personnel1_andersen_lab__iexact=value) |
                                                        Q(personnel2_andersen_lab__iexact=value) |
                                                        Q(personnel_knight_lab__iexact=value) |
                                                        Q(personnel_laurent_lab__iexact=value))
                    else:
                        q = q.filter(Q(personnel1_andersen_lab__iexact=value) |
                                     Q(personnel2_andersen_lab__iexact=value) |
                                     Q(personnel_knight_lab__iexact=value) |
                                     Q(personnel_laurent_lab__iexact=value))
                elif field == 'final_results':
                    if q == '':
                        q = test_results.objects.filter(final_results__iexact=value.strip())
                    else:
                        q = q.filter(final_results__iexact=value.strip())
                elif field == 'sample_bag_id':
                    if q == '':
                        q = test_results.objects.filter(sample_bag_id__iexact=value)
                    else:
                        q = q.filter(sample_bag_id__iexact=value)
                else:
                    continue

        if q == '':
            return render(request, 'qpcr_records/search_results.html')
        else:
            # Export query as table
            table = SearchResultsTable(q)
            RequestConfig(request).configure(table)
            export_format = request.GET.get('_export', None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response('table.{}'.format(export_format))

            return render(request, 'qpcr_records/search_results.html', {'table': table})


@login_required
def upload_qpcr_results(request):
    if request.method == 'GET':
        f = QPCRResultsUploadForm()
        return render(request, 'qpcr_records/upload_qpcr_results.html', {'form': f})
    else:
        f = QPCRResultsUploadForm(request.POST, request.FILES)

        if f.is_valid():
            # Parse file for Ct values and determine decision tree resuls
            file = request.FILES['qpcr_results_file']
            qrp_id = file.name.split('.')[0]
            exists = test_results.objects.filter(qrp_id=qrp_id)
            # Upload excel file to s3
            s3 = boto3.resource('s3', region_name=config('aws_s3_region_name'),
                                aws_access_key_id=config('aws_access_key_id'),
                                aws_secret_access_key=config('aws_secret_access_key'))
            s3.Bucket(config('aws_storage_bucket_name')).put_object(Key=file.name, Body=file)

            s3_filepath = config('aws_bucket_link') + file.name
            objs = test_results.objects.filter(qrp_id=qrp_id).update(file_transfer_status='Complete')
            objs = test_results.objects.filter(qrp_id=qrp_id).update(qpcr_results_file=s3_filepath)

            # update the database with values
            r = Results()
            data_ = r.get_results(file)
            r.read_fake_names()  # * Is this still needed?
            for well, vals in data_.items():
                if well != 'instrument':
                    objs = test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).update(
                        ms2_ct_value=vals['MS2'],
                        n_ct_value=vals['N gene'],
                        orf1ab_ct_value=vals['ORF1ab'],
                        s_ct_value=vals['S gene'],
                        decision_tree_results=vals['diagnosis'],
                        final_results=vals['diagnosis'],
                        qpcr_file_upload_time=datetime.now().strftime("%H:%M:%S"),
                        personnel_qpcr_file_upload=request.user.get_full_name())

                    if test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).count() > 0:
                        barcodes = \
                            test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).values_list('barcode', flat=True)[
                                0]
                        objs = test_results.objects.filter(qrp_id=qrp_id, rwp_well=well).update(
                            fake_name=r.get_fake_name(barcodes))
                elif well == 'instrument':
                    objs = test_results.objects.filter(qrp_id=qrp_id).update(qs5_id=vals)

            messages.success(request, mark_safe('qRT-PCR data uploaded successfully.'))
            return redirect('index')
        else:
            return render(request, 'qpcr_records/upload_qpcr_results.html', {'form': f})


@login_required()
def qpcr_plate_id_to_review(request):
    # Show initial form
    if request.method == 'GET':
        f = SelectQRPPlateForm()
        return render(request, 'qpcr_records/qpcr_plate_id_to_review.html', {'form': f})
    # Upon form submission, redirect to search_results if valid
    else:
        f = SelectQRPPlateForm(request.POST)

        if f.is_valid():
            request.session['qrp_id'] = f.cleaned_data['qrp_id']
            return redirect('review_results')
        else:
            # Show form again with errors
            return render(request, 'qpcr_records/qpcr_plate_id_to_review.html', {'form': f})


@login_required
def review_results(request):
    if request.method == 'GET':
        q = test_results.objects.filter(qrp_id__iexact=request.session['qrp_id'])
        table = ReviewTable(q)
        RequestConfig(request, paginate=False).configure(table)
        return render(request, 'qpcr_records/review_results.html', {'table': table, "choices": sample_result_choices})
    else:
        # Get wells
        qrp_id = request.session['qrp_id']
        qrp_wells = test_results.objects.filter(qrp_id__iexact=qrp_id).values_list('qrp_well', flat=True)

        # Get input from review form
        # - 1 to exclude CSRF token
        form_data = [request.POST[f"row{i}"] for i in range(len(request.POST) - 1)]

        # Update results and review status
        for qrp_well, choice in zip(qrp_wells, form_data):
            test_results.objects.filter(qrp_well=qrp_well, qrp_id__iexact=qrp_id).update(final_results=choice,
                                                                                         is_reviewed=True)

        messages.success(request, mark_safe(f'Review status updated for all samples in plate \"{qrp_id}\".'))
        return redirect('index')


@login_required
def sample_release(request):
    if request.method == 'GET':
        # Query all reviewed positive samples that have NOT been released
        q = test_results.objects.filter(final_results__iexact='Positive', is_reviewed__iexact='True',
                                        sample_release__iexact='False')
        table = SampleReleaseTable(q)
        RequestConfig(request, paginate=False).configure(table)

        sample_release = list(q.values_list('sample_release', flat=True))
        sample_release = ['true' if v is True else v for v in sample_release]
        sample_release = ['false' if v is False else v for v in sample_release]

        return render(request, 'qpcr_records/sample_release.html', {'table': table, 'sample_release': sample_release})
    else:
        form_data = [request.POST[f"release{i}"] for i in range(len(request.POST) - 1)]
        form_data = [True if v == 'true' else v for v in form_data]
        form_data = [False if v == 'false' else v for v in form_data]

        # Update query sample_release values
        q = list(test_results.objects.filter(final_results__iexact='Positive', is_reviewed__iexact='True',
                                             sample_release__iexact='False'))
        for entry, release_value in zip(q, form_data):
            entry.sample_release = release_value

        test_results.objects.bulk_update(q, ['sample_release'])

        messages.success(request, mark_safe(f'{len(form_data)} samples marked as released.'))
        return redirect('index')


@login_required
def discard_storage_bag(request):
    # Show initial form
    if request.method == 'GET':
        f = SelectBagForm()
        return render(request, 'qpcr_records/discard_storage_bag.html', {'form': f})
    # Upon form submission, redirect to search_results if valid
    else:
        f = SelectBagForm(request.POST)

        if f.is_valid():
            q = list(test_results.objects.filter(sample_bag_id__iexact=f.cleaned_data['sample_bag_id']))

            for entry in q:
                entry.sample_bag_is_stored = 'False'
            test_results.objects.bulk_update(q, ['sample_bag_is_stored'])

            messages.success(request, mark_safe(f'Bag status updated.'))
            return redirect('index')
        else:
            # Show form again with errors
            return render(request, 'qpcr_records/discard_storage_bag.html', {'form': f})
