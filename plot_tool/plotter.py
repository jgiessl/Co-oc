import getopt, sys
import numpy as np
import os
from matplotlib import gridspec
import json
import shutil
import multiprocessing as mp
import matplotlib
import time
matplotlib.use('Agg')
import matplotlib.pyplot as plt

format_defs = None
base_path = None
top_k = 10
create_ranking = False
create_dist = False
create_form = False
distinction_dict = dict()


def main(argv):
    begin = time.time()
    sep = os.sep
    handle_input(argv)
    global base_path
    global format_defs
    format_defs = read_data_from_json_file(base_path, 'wikidata_format_entities.json')
    global create_ranking
    global create_dist
    global create_form
    global top_k
    create_plot_folder(base_path)
    print('finished setting up plot folder at ' + base_path)
    if os.cpu_count() == 1:
        number_processes = 1
    else:
        number_processes = os.cpu_count() - 1
    print("using {} processes for plotting".format(number_processes))
    if create_form:

        # create format co-occurrence plots
        path_f = base_path + sep + 'format_co_occurrences'
        path_f_save = base_path + sep + 'plot' + sep + 'format_co_occurrences'

        # giving plotting tasks to child processes
        with mp.Pool(processes=number_processes) as pool:
            pool.starmap(pool_target_form, [(filename, path_f, path_f_save, format_defs, top_k)
                                            for filename in os.listdir(path_f)])
        print('finished format co-occurrence plots')
    if create_ranking:

        # create ranking plots
        path_r = base_path + sep + 'rankings'
        path_r_save = base_path + sep + 'plot' + sep + 'rankings'

        # giving plotting tasks to child processes
        with mp.Pool(processes=number_processes) as pool:
            pool.starmap(pool_target_rank, [(filename, path_r, path_r_save, format_defs)
                                            for filename in os.listdir(path_r)])
        print('finished ranking plots')
    if create_dist:

        # create distinction plots
        path_r = base_path + sep + 'rankings'
        path_d = base_path + sep + 'plot'
        make_distinction_plot(path_r, path_d)
        print('finished distinction plot')
    end = time.time()
    print("time spend on plotting: {} seconds".format(end - begin))


def pool_target_form(filename, path_f, path_f_save, format_def, top):
    """
    target function for the child processes
    :param filename: name of the file with the stored data
    :param path_f: path/to/folder where the the format co-occurrences are stored
    :param path_f_save: path/to/folder where the format co-occurring plots will be saved
    :param format_def: dictionary containing the information about file formats, i.e. wikidata-ID, -label, -URI
    :param top: number of the highest co-occurring formats which will be plotted
    """
    data = read_data_from_json_file(path_f, filename)
    make_format_plot(data, format_def, path_f_save, top)


def pool_target_rank(filename, path_r, path_r_save, format_def):
    """
    target function for the child processes
    :param filename: name of the file with the stored data
    :param path_r: path/to/folder where the rankings are stored
    :param path_r_save: path/to/folder where the rankings plots will be saved
    :param format_def: dictionary containing the information about file formats, i.e. wikidata-ID, -label, -URI
    """
    data = read_data_from_json_file(path_r, filename)
    make_rankings(data, format_def, path_r_save)


def handle_input(argv):
    """
    function to handle the console input
    :param argv: keyword-arguments given to the program
    """
    sep = os.sep
    global base_path
    if len(argv) == 1:
        usage()
    elif len(argv) == 2:
        if argv[1] == '-h' or argv[1] == '--help':
            usage()
        base_path = argv[1]
        argument_list = ['-r', '-d', '-f']
    else:
        base_path = argv[1]
        argument_list = argv[2:]
    # Options
    options = "hrdft:"

    # Long options
    long_options = ["help", "rank_plots", "distinction_plot", "format_plots", "top_k ="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argument_list, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                usage()
            elif currentArgument in ("-r", "--rank_plots"):
                global create_ranking
                create_ranking = True
                path = base_path + sep + 'rankings'
                if check_if_option_possible(path):
                    pass
                else:
                    print("the rankings folder does not contain any files")
                    usage()
            elif currentArgument in ("-d", "--distinction_plot"):
                global create_dist
                create_dist = True
                path = base_path + sep + 'rankings'
                if check_if_option_possible(path):
                    pass
                else:
                    print("the rankings folder does not contain any files")
                    usage()
            elif currentArgument in ("-f", "--format_plots"):
                global create_form
                create_form = True
                path = base_path + sep + 'format_co_occurrences'
                if check_if_option_possible(path):
                    pass
                else:
                    print("the format_co_occurrences folder does not contain any files")
                    usage()
            elif currentArgument in ("-t", "--top_k"):
                global top_k
                top_k = int(currentValue)

    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))


def usage():
    """
    Prints the usage of plotter.py to the console
    """
    string = "usage: plotter.py path/to/program_run -h -r -d -f -t <number>\n"
    string += "path/to/program_run: required argument - is the path to the save runs for which plots shall be created\n"
    string += "-h, --help: optional argument - prints this usage message\n"
    string += "-r, --rank_plots: optional argument - creates plots depicting the ranking of the environments\n"
    string += "-d, --distinction_plot: optional argument - creates a plot depicting the distinctiveness of the models\n"
    string += "-f, --format_plots: optional argument - creates bar chart displaying the highest co-occurring formats\n"
    string += "                                         for the individual formats. Per default the 5 highest\n"
    string += "-t, --top_k: optional argument - changes the default value of the previous option by the given number\n"
    print(string)
    sys.exit()


def check_if_option_possible(path):
    """
    Checks if the given run folder contains the necessary files for the gievn plot options
    :param path: path/to/the/run/folder
    """
    if len(os.listdir(path)) >= 1:
        return True
    else:
        return False


def read_data_from_json_file(path, filename):
    """
    Basic function for reading json files
    :param path: path/to/the/file
    :param filename: name of the file
    :return: data contained in the json file - dictionary
    """
    with open(os.path.join(path, filename), 'r', encoding='utf8',
              errors='ignore') as f:
        data = json.load(f)
    return data


def create_plot_folder(path):
    """
    Sets up the folders for saving the plots
    :param path: path/to/the/run/folder where the plot folder shall be created
    """
    sep = os.sep
    # set up plot file folder
    if 'plot' in os.listdir(path):
        try:
            pat = path + sep + 'plot' + sep
            shutil.rmtree(pat, ignore_errors=True)
        except OSError:
            print("Deletion of {0} failed".format(path + sep + 'plot' + sep))
    try:
        p = path + sep + 'plot'
        os.mkdir(p)
    except OSError as e:
        print(e)
        print("Creation of the directory {0} failed".format(path + sep + 'plot'))

    global create_ranking
    if create_ranking:
        try:
            p = path + sep + 'plot' + sep + 'rankings'
            os.mkdir(p)
        except OSError as e:
            print(e)
            print("Creation of the directory {0} failed".format(path + sep + 'plot' + sep + 'rankings'))
    global create_form
    if create_form:
        try:
            p = path + sep + 'plot' + sep + 'format_co_occurrences'
            os.mkdir(p)
        except OSError as e:
            print(e)
            print("Creation of the directory {0} failed".format(path + sep + 'plot' + sep + 'format_co_occurrences'))


def create_data_object_info_file(data, format_def, path):
    """
    Creates a text file containing information about the data-object
    :param data: dictionary containing the information about the data-object
    :param format_def: dictionary containing the information about file formats, i.e. wikidata-ID, -label, -URI
    :param path: path/to/folder/ where to save the information
    """
    string = ""
    string += str(data['name'])
    string += "\n"
    string += "number of files:  "
    string += str(data['number_files'])
    string += "\n"
    string += "number of files with unknown format: "
    string += str(data['number_unknown'])
    string += "\n"
    number_known = data['number_files'] - data['number_unknown']
    string += 'number of files with known format: '
    string += str(number_known)
    string += "\n"
    string += "contained formats: "
    string += "\n"
    for x in data['formats']:
        string += x
        string += " -"
        string += format_def[x]['formats']
        string += " -"
        string += format_def[x]['URI']
        string += "\n"
    filename = str(data['name']) + "_info.txt"
    with open(os.path.join(path, filename), 'w+', encoding='utf8',
              errors='ignore') as f:
        f.write(string)


def create_ranking_plot(ranking_map, name, path):
    """
    Function for creating the ranking plot for a data-object
    :param ranking_map: dictionary containing the information of the ranking for the two models
    :param name: name of the data-object
    :param path: path/to/the/folder where the plot will be saved
    """
    sep = os.sep
    path = path + sep + name + '.png'

    # deconstruct map into lists
    environments = []
    tf_idf_ranking = []
    co_occurrence_ranking = []
    added_ranking = []

    for x in ranking_map:
        environments.append(x)
        co_occurrence_ranking.append(ranking_map[x][0])
        tf_idf_ranking.append(ranking_map[x][1])
        added_ranking.append(ranking_map[x][2])

    # setting up the plot
    widthscale_1 = 2 * len(environments)
    fig = plt.figure(figsize=(widthscale_1, 6))
    width = 0.25
    ax = plt.subplot()
    fig.add_axes(ax)

    x_indexes = np.arange(len(environments))
    bar1 = ax.bar(x_indexes - width, co_occurrence_ranking, width=width, label='co-occurrence')
    bar2 = ax.bar(x_indexes, tf_idf_ranking, width=width, label='tf-idf')
    bar3 = ax.bar(x_indexes + width, added_ranking, width=width, label='combined-mean')
    ax.set_title("Environment Rankings of {0}".format(name))
    ax.set_xlabel("Environments")
    ax.set_ylabel("Relative Ranking Score")
    ax.set_xticks(x_indexes)
    ax.set_xticklabels(environments)
    ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='x-small')

    def auto_label(bars):
        """Attach a text label above each bar, displaying its height."""
        for bar in bars:
            height = round(bar.get_height(), 2)
            ax.annotate('{}'.format(height),
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    auto_label(bar1)
    auto_label(bar2)
    auto_label(bar3)

    # saving figure
    plt.subplots_adjust(wspace=0.6)
    plt.tight_layout(pad=3.0)
    fig.savefig(path, format='png')
    plt.close(fig)


def make_rankings(data, format_def, path_r):
    """
    Creates the ranking plot and the information file for a given data-object
    :param data: dictionary holding the information about the data-object
    :param format_def: dictionary containing the information about file formats, i.e. wikidata-ID, -label, -URI
    :param path_r: path/to/the/folder where the files are saved
    """
    # creating information file
    create_data_object_info_file(data, format_def, path_r)

    # formatting the rankings for the plot
    name = data['name']
    ranking_map = data['environments']
    formatted_ranking_map = dict()
    for key in ranking_map:
        tmp = list()
        tmp.append(ranking_map[key]['co-oc'])
        tmp.append(ranking_map[key]['tf-idf'])
        tmp.append(ranking_map[key]['combined'])
        formatted_ranking_map[key] = tmp
    # creating plot
    create_ranking_plot(formatted_ranking_map, name, path_r)


def create_format_info_file(name, formats, format_def, path):
    """
    Creates a text file containing information about the data-object
    :param name: name of the format, i.e. wikidata-ID
    :param formats: highest co-occurring formats for the format 'name' - wikidata-IDs
    :param format_def: dictionary containing the information about file formats, i.e. wikidata-ID, -label, -URI
    :param path: path/to/folder/ where to save the information
    """
    string = name
    string += " -"
    string += format_def[name]['formats']
    string += " -"
    string += format_def[name]['URI']
    string += "\n"
    string += "\n"
    n = len(string)
    string += "#"*n
    string += "\n"
    string += "\n"
    for x in formats:
        string += x
        string += " -"
        string += format_def[x]['formats']
        string += " -"
        string += format_def[x]['URI']
        string += "\n"

    filename = name + "_info.txt"
    with open(os.path.join(path, filename), 'w+', encoding='utf8',
              errors='ignore') as f:
        f.write(string)


def make_format_plot(data, format_def, path, top):
    """
    Function to create the format -occurrence plots and the information files of the formats
    :param data: dictionary containing the normalized co-occurrence scores for each co-occurring format
    :param format_def: dictionary containing the information about file formats, i.e. wikidata-ID, -label, -URI
    :param path: path/to/the/folder where the files will be saved
    :param top: number of the highest co-occurring formats which will be plotted
    """

    # calculating the highest co-occurring formats
    tmp = list()
    name = None
    for key in data:
        if key == "name":
            name = data[key]
        elif key == "type":
            continue
        else:
            tempo = list()
            tempo.append(key)
            tempo.append(data[key]["object"])
            tempo.append(data[key]["dictionary"])
            tempo.append(data[key]["combined"])
            tmp.append(tempo)
    sort_list = sorted(tmp, key=lambda tup: tup[3], reverse=True)
    if len(sort_list) == 0:
        print("cannot plot co-occurrences because the format {} does not co-occur with other known "
              "formats".format(name))
        return

    if len(sort_list) <= top:
        formated_list = sort_list
    else:
        formated_list = sort_list[:top]

    # formatting the results for the plot
    formats = list()
    values = list()
    values_d = list()
    values_c = list()
    for x in formated_list:
        formats.append(x[0])
        values.append(x[1])
        values_d.append(x[2])
        values_c.append(x[3])

    create_format_info_file(name, formats, format_def, path)
    create_plot_for_format_co_occurrences(formats, values, values_d, values_c, name, path)


def create_plot_for_format_co_occurrences(formats, values, values_d, values_c, name, path):
    """
    Creates a plot showing the score values of the co-occurring formats for a format
    :param formats: List of formats co-occurring with a format
    :param values: Score values (normalized) of the co-occurrences of the formats in data-objects
    :param values_d: Score values (normalized) of the co-occurrences of the formats in directories.
    :param values_c: Score values (normalized) co-occurrences of the formats in data-objects and directories
                     combined.
    :param name: Format for which the co-occurring formats will be plotted
    :param path: path/to/folder where the plot will be saved
    """
    # setting up paths and directories
    sep = os.sep
    path = path + sep + name + '.png'

    widthscale = top_k

    # plotting
    width = 0.25
    f, ax = plt.subplots()
    f.set_size_inches(widthscale + 0.3, 6)
    x_indexes = np.arange(len(formats))
    ax.bar(x_indexes - width, values, width=width, label='in data-objects')
    ax.bar(x_indexes, values_d, width=width, label='in directories')
    ax.bar(x_indexes + width, values_c, width=width, label='combined')
    ax.set_xlabel('Formats')
    ax.set_ylabel('Co-occurrence Score with {0}'.format(name))
    ax.set_title('Co-occurring formats for ' + name)
    ax.set_xticks(x_indexes)
    ax.set_xticklabels(formats)
    ax.margins(0.01)
    plt.xticks(rotation=90, fontsize=7)
    ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='x-small')
    plt.tight_layout(pad=3.0)
    plt.savefig(path, format='png', bbox_inches="tight")
    plt.close(f)


def make_distinction_plot(path_r, path_save):
    """
    Function calculates the distinctiveness of the rankings and plots them
    :param path_r: path/to/folder where the rankings of the run are saved
    :param path_save: path/to/folder where the plot will be saved
    """

    # setting up the the dictionary containing the distinctiveness
    global distinction_dict
    for filename in os.listdir(path_r):
        data = read_data_from_json_file(path_r, filename)
        n = len(data['formats'])
        ranking_map = data['environments']
        co_oc = list()
        tf_idf = list()
        for key in ranking_map:
            co_oc.append(ranking_map[key]['co-oc'])
            tf_idf.append(ranking_map[key]['tf-idf'])
        s_co_oc = sorted(co_oc, reverse=True)
        s_tf_idf = sorted(tf_idf, reverse=True)
        diff_co_oc = s_co_oc[0] - s_co_oc[1]
        diff_tf_idf = s_tf_idf[0] - s_tf_idf[1]
        if n not in distinction_dict:
            distinction_dict[n] = [diff_co_oc, diff_tf_idf, 1]
        else:
            distinction_dict[n][0] += diff_co_oc
            distinction_dict[n][1] += diff_tf_idf
            distinction_dict[n][2] += 1

    # calculating the mean differences of the highest and second highest ranked environment.
    # and formatting the results for the plot
    mean_list = list()
    for key in distinction_dict:
        tmp = list()
        tmp.append(key)
        mean_co_oc = distinction_dict[key][0] / distinction_dict[key][2]
        mean_tf_idf = distinction_dict[key][1] / distinction_dict[key][2]
        tmp.append(mean_co_oc)
        tmp.append(mean_tf_idf)
        mean_list.append(tmp)
    sort_mean_list = sorted(mean_list, key=lambda tupl: tupl[0])
    number_formats = list()
    co_oc_mean_diff = list()
    tf_idf_mean_diff = list()
    for x in sort_mean_list:
        number_formats.append(x[0])
        co_oc_mean_diff.append(x[1])
        tf_idf_mean_diff.append(x[2])

    # calculating overall distinctiveness
    count = 0
    sum_diff_co_oc = 0
    sum_diff_tf_idf = 0
    for key in distinction_dict:
        count += distinction_dict[key][2]
        sum_diff_co_oc += distinction_dict[key][0]
        sum_diff_tf_idf += distinction_dict[key][1]
    mean_co_oc_all = sum_diff_co_oc / count
    mean_tf_idf_all = sum_diff_tf_idf / count

    # making the plot
    tup = [number_formats, co_oc_mean_diff, tf_idf_mean_diff, mean_co_oc_all, mean_tf_idf_all]
    create_distinction_plot(tup, path_save)


def create_distinction_plot(tup, path):
    """
    Creates a plot which shows the the mean differences of the relative scores between
    the highest and the second highest ranked environment for both tf-idf and co-occurrence ranking
    in relation to the number of known formats of the data-objects
    :param tup: contains the number of formats the mean difference in co-occurrence-ranking
                and the mean difference in tf-idf ranking
                ([number_formats], [mean diff co-oc], [mean diff tf-idf], overall mean diff co-oc,
                overall mean diff co-oc)
    """
    sep = os.sep
    number_formats, distinct_co, distinct_tf = tup[0], tup[1], tup[2]
    all_dist_co_oc = tup[3]
    all_dist_tf_idf = tup[4]

    # formatting data for the plots
    n = len(number_formats)
    m = max(number_formats)
    new_nf = np.arange(m + 1)
    new_dis_co = np.zeros(m + 1)
    new_dis_tf = np.zeros(m + 1)
    for x in range(n):
        y = number_formats[x]
        co = distinct_co[x]
        tf = distinct_tf[x]
        new_dis_co[y] = co
        new_dis_tf[y] = tf

    # setting up the plots
    widthscale = n / 5
    widthscale_2 = widthscale / 4
    width = 0.4
    fig = plt.figure(figsize=(widthscale + widthscale_2 + 2, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[widthscale, widthscale_2])
    fig.suptitle('Distinctiveness of first rated to second rated environment')
    ax = plt.subplot(gs[0])
    ax1 = plt.subplot(gs[1])

    ax.bar(new_nf - width / 2, new_dis_co, width=width, label='co-occurrence')
    ax.bar(new_nf + width / 2, new_dis_tf, width=width, label='tf-idf')
    ax.set_xlabel('number of formats in data object')
    ax.set_ylabel('mean difference between first and second choice')
    ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='x-small')

    ax1.bar(1 - width / 2, all_dist_co_oc, width=width, label='co-occurrence')
    ax1.bar(1 + width / 2, all_dist_tf_idf, width=width, label='tf-idf')
    ax1.set_ylabel('mean difference between first and second choice')
    ax1.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='x-small')
    ax1.set_xticks([])

    # saving figure
    path = path + sep + 'distinction' + '.png'
    plt.tight_layout(pad=3.0)
    plt.savefig(path, format='png')
    plt.close(fig)


if __name__ == "__main__":
    main(sys.argv)

