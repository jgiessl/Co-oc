import getopt
import sys
import numpy as np
import os
import json
import multiprocessing as mp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(argv):
    base_path = os.path.dirname(os.path.abspath(__file__))
    top_n = 5
    sep = os.sep
    if len(argv) <= 1:
        usage()
    else:
        argument_list = argv[1:]
    # Options
    options = "ht:"

    # Long options
    long_options = ["help", "top_n ="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argument_list, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                usage()
            elif currentArgument in ("-t", "--top_n"):
                top_n = int(currentValue)

    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))

    path_r = argv[-1]
    if os.cpu_count() == 1:
        number_processes = 1
    else:
        number_processes = os.cpu_count() - 1
    print("using {} processes for plotting".format(number_processes))

    # create ranking plots
    path_r_save = base_path + sep + 'ranking_plots'
    # giving plotting tasks to child processes
    with mp.Pool(processes=number_processes) as pool:
        pool.starmap(pool_target_rank, [(filename, path_r, path_r_save, top_n) for filename in os.listdir(path_r)])
    print('finished ranking plots')


def pool_target_rank(filename, path_r, path_r_save, top_n):
    """
    target function for the child processes
    :param filename: name of the file with the stored data
    :param path_r: path/to/folder where the rankings are stored
    :param path_r_save: path/to/folder where the rankings plots will be saved
    :param top_n: number of highest ranking environments included in the plots
    """
    data = read_data_from_json_file(path_r, filename)
    make_rankings(data, path_r_save, top_n)


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


def create_ranking_plot(ranking_list, name, path):
    """
    Function for creating the ranking plot for a data-object
    :param ranking_list: list containing the top ranked environments [name, score]
    :param name: name of the data-object
    :param path: path/to/the/folder where the plot will be saved
    """
    sep = os.sep
    path = path + sep + name + '.png'

    # deconstruct map into lists
    environments = []
    co_occurrence_ranking = []

    for x in ranking_list:
        environments.append(x[2])
        co_occurrence_ranking.append(x[1])

    # setting up the plot
    if len(environments) < 4:
        widthscale_1 = 2 * 4
    else:
        widthscale_1 = 2 * len(environments)
    fig = plt.figure(figsize=(widthscale_1, 6))
    width = 0.25
    ax = plt.subplot()
    fig.add_axes(ax)

    x_indexes = np.arange(len(environments))
    bar1 = ax.bar(x_indexes, co_occurrence_ranking, width=width, label='co-occurrence')
    ax.set_title("Environment Rankings of {0}".format(name))
    ax.set_xlabel("Environments")
    ax.set_ylabel("Ranking Score")
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

    # saving figure
    plt.subplots_adjust(wspace=0.6)
    plt.tight_layout(pad=3.0)
    fig.savefig(path, format='png')
    plt.close(fig)


def make_rankings(data, path_r_save, top_n):
    """
    Creates the ranking plot and the information file for a given data-object
    :param data: dictionary holding the information about the data-object
    :param path_r_save: path/to/the/folder where the files are saved
    :param top_n: number of highest ranking environments included in the plots
    """
    # formatting the rankings for the plot
    name_pre = data['filename']
    name = name_pre.split(".").pop(0)
    ranking_list = []
    env_counter = 0
    for key in data:
        if key == 'filename' or key == 'formats' or key == 'number_unknown_files' or key == 'number_files':
            continue
        if data[key]['co-oc'] <= 0:
            continue
        ranking_list.append([key, data[key]['co-oc'], env_counter])
        env_counter += 1
    if len(ranking_list) == 0:
        print('None of given environments are appropriate for file {0} ,i.e. all scores are 0'.format(data['filename']))
        return
    ranking_list_sorted = sorted(ranking_list, key=lambda y: y[1], reverse=True)
    top_list = ranking_list_sorted[:top_n]
    create_ranking_plot(top_list, name, path_r_save)
    create_data_object_info_file(data['filename'], data['formats'], data['number_unknown_files'], data['number_files'],
                                 path_r_save, top_list)


def create_data_object_info_file(filename, formats, number_unknown_files, number_files, path, top_list):
    string = ""
    string += filename
    string += "\n"
    string += "top ranked environments: "
    string += "\n"
    for x in top_list:
        string += "environment_number: {0}; environment_name: {1}; score: {2}".format(x[2], x[0], x[1])
        string += "\n"
    string += "\n"
    string += "number of files:  "
    string += str(number_files)
    string += "\n"
    string += "number of files with unknown format: "
    string += str(number_unknown_files)
    string += "\n"
    number_known = number_files - number_unknown_files
    string += 'number of files with known format: '
    string += str(number_known)
    string += "\n"
    rate = number_known / number_files
    string += "rate of files with known format: "
    string += str(rate)
    string += "\n"
    string += "contained formats: "
    string += "\n"
    for x in formats:
        string += "id: {0}; format {1}".format(x[0], x[1])
        string += "\n"
    name = filename.split(".").pop(0) + "_info.txt"
    with open(os.path.join(path, name), 'w+', encoding='utf8',
              errors='ignore') as f:
        f.write(string)


def usage():
    """
    Prints the usage of plotter.py to the console
    """
    string = "usage: plotter.py -h -t <number> path/to/program_run\n"
    string += "path/to/program_run: required argument - is the path to the save runs for which plots shall be created\n"
    string += "-h, --help: optional argument - prints this usage message\n"
    string += "-t, --top_n: optional argument - number of highest ranking environments to be plotted\n"
    print(string)
    sys.exit()


if __name__ == '__main__':
    main(sys.argv)

