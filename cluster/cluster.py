import scipy.sparse as sp
from sklearn.preprocessing import normalize
import os
import json
from json.decoder import JSONDecodeError
import itertools
from enum import Enum
import math
import numpy as np
import multiprocessing as mp
import matplotlib
matplotlib.use('Agg')
import networkx as nx
import matplotlib.pyplot as plt
import getopt
import sys

top_k = 10
base_path = ''


class MatrixType(Enum):
    global_mat = 1
    global_directory_mat = 2


class ObjectClusterProcessor:

    def __init__(self):

        # Map of Wikidata-IDs to Integer-Ids
        self.formatIdMap = {}

        # Map of Integer-Ids to Wikidata-Ids
        self.formatIdMap_reverse = {}

        self.formatIdCounter = 0

        # Stores the number of co-occurrences of the formats in respect to the Data-objects.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.gCOM = {}  # gCOM -> global-Co-Occurrence-Matrix, i.e. bias matrix for objects

        # Stores the number of co-occurrences of the formats in respect to the folders of all Data-objects.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.gdCOM = {}  # gdCOM -> global-directory-Co-Occurrence-Matrix, i.e bias matrix for directories

        self.file_counter = 0
        self.unknown_counter = 0

        self.format_legend = {}



    def add_to_COM(self, id_1, id_2, matrix_type):
        """
        Helper function for building the matrices which store the frequencies of the format co-occurrences
        :param id_1: Id of the first format of the combination
        :param id_2: Id of the second format of the combination
        :param matrix_type: gives the type of the reference matrix, i.e.
                            MatrixType.global_directory_mat : Stores the co-occurrences of formats in the directories
                                                             of all the data-object
                            MatrixType.global_mat : Stores the co-occurrences of formats in
                                                              all the data-object
        :param mode: Mode of the program, i.e. does program run use PUID or Wikidata-ID
        """
        if matrix_type == MatrixType.global_directory_mat:
            reference_matrix = self.gdCOM
        else:
            reference_matrix = self.gCOM
        if id_1 == id_2:
            return
        if id_2 < id_1:
            id_2, id_1 = id_1, id_2
        if (id_1, id_2) not in reference_matrix:
            reference_matrix[(id_1, id_2)] = 1
            reference_matrix[(id_2, id_1)] = 1
        else:
            reference_matrix[(id_1, id_2)] += 1
            reference_matrix[(id_2, id_1)] += 1

    def add_format_id(self, file_format):
        """
        Adds file format to an index map
        :param file_format: Wikidata-ID of the file
        """
        if file_format not in self.formatIdMap:
            self.formatIdMap[file_format] = self.formatIdCounter
            self.formatIdMap_reverse[self.formatIdCounter] = file_format
            self.formatIdCounter += 1


    def create_csc_matrix_from_dict(self, dictionary):
        """
        Creates a csc- matrix from a dictionary where the
        :param dictionary: dictionary which shall be turned into a csc-matrix
        :return: csc- matrix
        """
        dim = self.formatIdCounter
        rows, cols, vals = [], [], []
        for key, value in dictionary.items():
            rows.append(key[0])
            cols.append(key[1])
            vals.append(value)
        x = sp.csc_matrix((vals, (rows, cols)), shape=(dim, dim))
        return x

    @staticmethod
    def calculate_relative_weight_matrix(csc_matrix):
        """
        Normalizes the co-occurrences for a given matrix in csc-format
        :param csc_matrix: Matrix to be normalized
        :return: Normalized co-occurrence matrix
        """
        col_weight_normalized = normalize(csc_matrix, norm='l1', axis=0)
        x = (col_weight_normalized.transpose().multiply(col_weight_normalized))
        return x.sqrt()

    @staticmethod
    def get_directory(filepath):
        """
        Gets the directory of the data object which contains the given file
        :param filepath: Path/To/the/File/In/Object
        :param filename: Name of the File
        :return: Directory of file in a data object
        """
        temp = filepath.replace("\\", "/")
        tmp = temp.split("/")
        if len(tmp) == 1:
            return 'root'
        else:
            del tmp[-1]
            return "/".join(tmp)

    @staticmethod
    def get_file_format_combinations(list_of_sets):
        """
        Calculates all possible format combinations of length 2 from a given context
        :param list_of_sets: list of formats in the same context
        :return: List of tuples representing the possible combinations
        """
        l = []
        for x in list_of_sets:
            if len(x) <= 1:
                continue
            y = list(x)
            tmp = []
            for z in itertools.combinations(y, 2):
                z = list(z)
                tmp.append(z)
            l.append(tmp)
        return l

    def pre_process_data_objects(self, path_to_objects):
        """
        Function which processes all the data objects in a given location
        and builds the matrices representing the format co-occurrences of the object corpus
        :param path_to_objects: Path/To/Objects
        """
        for filename in os.listdir(path_to_objects):
            with open(os.path.join(path_to_objects, filename), 'r', encoding='utf8',
                      errors='ignore') as f:
                try:
                    data = json.load(f)
                except JSONDecodeError:
                    print('### Could not decode Jason {0}'.format(filename))
                    continue
                files = data["files"]
                if len(files) == 0:
                    print("### Siegfried-output of {0} doesn't have any files".format(filename))
                    continue
                if len(data["identifiers"]) > 1:
                    print("program currently cannot handle multiple identifiers at the same time.")
                    continue
                elif len(data["identifiers"]) < 1:
                    print("no identifiers are specified in siegfried output.")
                    continue

                tmp = []

                # For collecting all the possible formats of a data object
                object_common_formats = set()

                # For collecting all the possible formats of directories in a data object
                directory_common_formats = dict()

                # parsing and sorting of the files
                for x in files:
                    self.file_counter += 1
                    name = x["filename"]
                    possible_formats = x["matches"]
                    formats = set()
                    for y in possible_formats:
                        if y["id"] == 'UNKNOWN':
                            self.unknown_counter += 1
                            continue
                        if y["id"] not in self.format_legend:
                            self.format_legend[y["id"]] = y["format"]
                        self.add_format_id(y["id"])
                        formats.add(self.formatIdMap[y["id"]])
                    directory = self.get_directory(name)
                    if directory in directory_common_formats:
                        directory_common_formats[directory] = directory_common_formats[directory].union(formats)
                    else:
                        directory_common_formats[directory] = formats
                    object_common_formats = object_common_formats.union(formats)
                for key, value in directory_common_formats.items():
                    tmp.append(value)
                directory_format_combinations = self.get_file_format_combinations(tmp)
                object_format_combinations = self.get_file_format_combinations([list(object_common_formats)])

                # adding the co-occurrences the the matrices
                for x in directory_format_combinations:
                    for y in x:
                        self.add_to_COM(y[0], y[1], MatrixType.global_directory_mat)
                for x in object_format_combinations:
                    for y in x:
                        self.add_to_COM(y[0], y[1], MatrixType.global_mat)

    def get_parameters(self, path, filename):
        """
        Extracts parameters from jason file
        :param path: Path/To/File
        :param filename: Name of the file
        :return: dictionary of parameters
        """
        with open(os.path.join(path, filename), 'r', encoding='utf8', errors='ignore') as f:
            data = json.load(f)
            return data

    @staticmethod
    def build_dictionary_from_csc_matrix(csc_matrix):
        """
        Function which takes a matrix in csc-format and creates a dictionary representing the matrix
        :param csc_matrix: matrix in csc-format
        :return: matrix in a dictionary representation {(row-index, col-index): value}
        """
        p_m_coo = csc_matrix.tocoo()
        pmf = list(zip(p_m_coo.row, p_m_coo.col, p_m_coo.data))
        processed_matrix_formatted = dict()
        for x in pmf:
            processed_matrix_formatted[(x[0], x[1])] = x[2]
        return processed_matrix_formatted


class Visualizer:

    def __init__(self):
        self.formatIdMap = {}
        self.formatIdMap_reverse = {}

        self.alpha = 0
        self.beta = 0

        self.norm_object_matrix = {}
        self.norm_directory_matrix = {}
        self.formatIdCounter = 0

        self.format_co_occurrence_storage = {}


    def create_cluster_matrix(self):
        max_val = 0
        help_dict = {}
        for key_pair, value in self.norm_object_matrix.items():
            if key_pair not in help_dict:
                help_dict[key_pair] = self.alpha * value
                if help_dict[key_pair] > max_val:
                    max_val = help_dict[key_pair]
            else:
                help_dict[key_pair] += self.alpha * value
                if help_dict[key_pair] > max_val:
                    max_val = help_dict[key_pair]

        for key_pair, value in self.norm_directory_matrix.items():
            if key_pair not in help_dict:
                help_dict[key_pair] = self.beta * value
                if help_dict[key_pair] > max_val:
                    max_val = help_dict[key_pair]
            else:
                help_dict[key_pair] += self.beta * value
                if help_dict[key_pair] > max_val:
                    max_val = help_dict[key_pair]
        adj_mat = {}
        x_sum = 0
        x_square_sum = 0
        for key_pair, value in help_dict.items():
            key_pair_new = (self.formatIdMap_reverse[key_pair[0]], self.formatIdMap_reverse[key_pair[1]])
            key_pair_new_inv = (self.formatIdMap_reverse[key_pair[1]], self.formatIdMap_reverse[key_pair[0]])
            if (key_pair_new not in adj_mat) and (key_pair_new_inv not in adj_mat):
                norm = (value / max_val)
                adj_mat[key_pair_new] = norm
                x_sum += norm
                x_square_sum += norm**2
        if len(adj_mat) == 0:
            expec = 0
            st_dev = 0
        else:
            expec = x_sum / len(adj_mat)
            st_dev = math.sqrt((x_square_sum / len(adj_mat)) - expec**2)
        return adj_mat, expec, st_dev

    def visualize_cluster(self, path):
        tup = self.create_cluster_matrix()
        g = nx.Graph()
        for key_pair, value in tup[0].items():
            g.add_edge(key_pair[0], key_pair[1], weight=value)

        esmall = [(u, v) for (u, v, d) in g.edges(data=True) if d["weight"] <= tup[1]]
        em = [(u, v) for (u, v, d) in g.edges(data=True) if (d["weight"] <= tup[1] + tup[2]) and (d["weight"] > tup[1])]
        elarge = [(u, v) for (u, v, d) in g.edges(data=True) if d["weight"] > tup[1] + tup[2]]
        pos = nx.spring_layout(g, weight='weight')
        plt.figure(figsize=(12, 8))
        nx.draw_networkx_nodes(g, pos, node_size=300, alpha=0)

        nx.draw_networkx_edges(g, pos, edgelist=elarge, edge_color='r', alpha=0.5)
        nx.draw_networkx_edges(g, pos, edgelist=em, edge_color='g', alpha=0.25)
        nx.draw_networkx_edges(g, pos, edgelist=esmall, edge_color='b', alpha=0.125)

        nx.draw_networkx_labels(g, pos, font_size=7)

        plt.axis("off")
        plt.savefig(path, format='png')

    @staticmethod
    def create_plot_for_format_co_occurrences(formats, values, values_d, values_c, name, path, top):
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
        name = name.replace("/", "#")
        path = path + sep + name + '.png'
        widthscale = top

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

    def make_format_plot(self, data, path, top):
        """
        Function to create the format co-occurrence plots and the information files of the formats
        :param data: dictionary containing the normalized co-occurrence scores for each co-occurring format
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

        self.create_plot_for_format_co_occurrences(formats, values, values_d, values_c, name, path, top)

    def pool_target_form(self, format_name, path_f_save, top):
        """
        target function for the child processes
        :param format_name: name of the format for which co-occurrences plots will be made
        :param path_f_save: path/to/folder where the format co-occurring plots will be saved
        :param top: number of the highest co-occurring formats which will be plotted
        """
        data = self.format_co_occurrence_storage[format_name]
        self.make_format_plot(data, path_f_save, top)

    def global_format_co_occurrences(self, csc_preprocess_matrix_g, csc_preprocess_matrix_d
                                     , csc_preprocess_matrix_c):
        """
        Calculates the lists of co-occurrences for all known formats for visualisation
        """
        mat_dim = csc_preprocess_matrix_g.get_shape()[0]
        for x in range(mat_dim):
            n_values = []
            n_values_d = []
            n_values_c = []

            col = csc_preprocess_matrix_g.getcol(x).toarray().flatten()
            col_d = csc_preprocess_matrix_d.getcol(x).toarray().flatten()
            col_c = csc_preprocess_matrix_c.getcol(x).toarray().flatten()
            values = []
            values_d = []
            values_c = []
            formats = []
            for y in range(mat_dim):
                val = col[y]
                val_d = col_d[y]
                val_c = col_c[y]
                if val != 0:
                    format_name = self.formatIdMap_reverse[y]
                    formats.append(format_name)
                    values.append(val)
                    values_d.append(val_d)
                    values_c.append(val_c)
                if y == mat_dim - 1:
                    if len(values) == 0:
                        form = self.formatIdMap_reverse[x]
                        print("Format {0} ".format(form)
                              + "does not co-occur in data objects with other known formats")

                    else:
                        # normalizing
                        sum_g = 0
                        sum_d = 0
                        sum_c = 0
                        for z in range(len(values)):
                            sum_g += values[z]
                            sum_d += values_d[z]
                            sum_c += values_c[z]
                        if sum_d == 0:
                            for z in values_d:
                                n_values_d.append(z)
                        else:
                            for z in values_d:
                                n_values_d.append(z / sum_d)
                        for z in values:
                            n_values.append(z / sum_g)
                        for z in values_c:
                            n_values_c.append(z / sum_c)

                        form = self.formatIdMap_reverse[x]
                        self.format_co_occurrence_storage[form] = self.create_dictionary_for_json(formats,
                                                                                                  n_values,
                                                                                                  n_values_d,
                                                                                                  n_values_c,
                                                                                                  form)

    @staticmethod
    def create_dictionary_for_json(formats, n_values, n_values_d, n_values_c, form):
        serialize = dict()
        serialize['name'] = form
        for i in range(len(formats)):
            tmp = dict()
            tmp['object'] = n_values[i]
            tmp['dictionary'] = n_values_d[i]
            tmp['combined'] = n_values_c[i]
            serialize[formats[i]] = tmp
        return serialize


def main(argv):
    global base_path
    sep = os.sep
    handle_input(argv)
    ocp = ObjectClusterProcessor()
    data = ocp.get_parameters(os.path.dirname(os.path.abspath(__file__)), "config.json")

    ocp.pre_process_data_objects(base_path)
    cur_path = os.path.dirname(os.path.abspath(__file__))

    n_object_matrix = ocp.calculate_relative_weight_matrix(ocp.create_csc_matrix_from_dict(ocp.gCOM))
    n_directory_matrix = ocp.calculate_relative_weight_matrix(ocp.create_csc_matrix_from_dict(ocp.gdCOM))
    visu = Visualizer()
    visu.formatIdMap = ocp.formatIdMap
    visu.formatIdMap_reverse = ocp.formatIdMap_reverse
    visu.formatIdCounter = ocp.formatIdCounter
    visu.norm_object_matrix = ocp.build_dictionary_from_csc_matrix(n_object_matrix)
    visu.norm_directory_matrix = ocp.build_dictionary_from_csc_matrix(n_directory_matrix)
    visu.alpha = data['global']
    visu.beta = data['global_dir']
    comb = visu.alpha * n_object_matrix + visu.beta * n_directory_matrix
    if os.cpu_count() == 1:
        number_processes = 1
    else:
        number_processes = os.cpu_count() - 1
    print("using {} processes for plotting".format(number_processes))

    path_f_save = cur_path + sep + 'plots' + sep + 'bar_plots'
    try:
        os.mkdir(path_f_save)
    except OSError as e:
        print(e)
        print("Creation of the directory {0} failed".format(path_f_save))
    visu.global_format_co_occurrences(n_object_matrix, n_directory_matrix, comb)
    with mp.Pool(processes=number_processes) as pool:
        pool.starmap(visu.pool_target_form, [(format_name, path_f_save, top_k)
                                             for format_name in visu.format_co_occurrence_storage])
    path_save = cur_path + sep + 'plots' + sep + 'cluster' + '.png'
    visu.visualize_cluster(path_save)
    path_info = cur_path + sep + 'plots'
    create_info_file(path_info, ocp.format_legend, ocp.file_counter, ocp.unknown_counter)


def create_info_file(path, format_map, number_files, number_unknown):
    file = "info.txt"
    string = ""
    string += "Number of files in data set: {} \n".format(number_files)
    string += "Number of files with unknown format in data set: {} \n".format(number_unknown)
    rate = (number_files - number_unknown) / number_files
    string += "Rate of files with known format: {} \n".format(rate)
    string += " \n"
    tmp = []
    for x in format_map:
        tmp.append(x)
    temp = sorted(tmp)
    for x in temp:
        string += x
        string += ": "
        string += format_map[x]
        string += " \n"
    with open(os.path.join(path, file), 'w+', encoding='utf8', errors='ignore') as info_file:
        info_file.write(string)


def handle_input(argv):
    """
    function to handle the console input
    :param argv: keyword-arguments given to the program
    """
    global base_path
    if len(argv) == 1:
        usage()
    elif len(argv) == 2:
        if argv[1] == '-h' or argv[1] == '--help':
            usage()
        base_path = argv[1]
        argument_list = []
    else:
        base_path = argv[1]
        argument_list = argv[2:]
    # Options
    options = "ht:"

    # Long options
    long_options = ["help", "top_k ="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argument_list, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
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
    string = "usage: cluster.py path/to/program_run -h -t <number>\n"
    string += "path/to/collection/siegfried/json/of/data-objects/: required argument\n"
    string += "-h, --help: optional argument - prints this usage message\n"
    string += "-t, --top_k: optional argument - given number = max number of highest co-occurring formats in bar-plot\n"
    print(string)
    sys.exit()


if __name__ == "__main__":
    main(sys.argv)




