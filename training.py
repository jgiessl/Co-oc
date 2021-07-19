import scipy.sparse as sp
from sklearn.preprocessing import normalize
import os
import json
from json.decoder import JSONDecodeError
import itertools
from enum import Enum
from ast import literal_eval as mt
import time
import getopt
import sys


class ObjectTrainProcessor:

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

        self.pronom_changed = False

        self.wiki_changed = False

        # Map of PUIDS to Integer-Ids
        self.formatIdMap_puid = {}

        # Map of Integer-Ids to PUIDs
        self.formatIdMap_reverse_puid = {}

        self.formatIdCounter_puid = 0

        # Stores the number of co-occurrences of the formats in respect to the Data-objects.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.gCOM_puid = {}  # gCOM -> global-Co-Occurrence-Matrix, i.e. bias matrix for objects

        # Stores the number of co-occurrences of the formats in respect to the folders of all Data-objects.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.gdCOM_puid = {}  # gdCOM -> global-directory-Co-Occurrence-Matrix, i.e bias matrix for directories

        # stores the format ids (Integer) of the current data object
        # self.formats_of_current_data = set()

        # format frequencies in the objects
        self.df_map = {}
        self.df_map_puid = {}

        # number of files in the objects
        self.document_lengths = []
        self.document_lengths_puid = []

        # number of objects in the training set
        self.number_objects = 0
        self.number_objects_puid = 0

    def add_to_COM(self, id_1, id_2, matrix_type, mode):
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
            if mode == Mode.pronom:
                reference_matrix = self.gdCOM_puid
            else:
                reference_matrix = self.gdCOM
        else:
            if mode == Mode.pronom:
                reference_matrix = self.gCOM_puid
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

    def add_format_id_puid(self, file_format):
        """
        Adds file format to an index map
        :param file_format: PUID-ID of the file
        """
        if file_format not in self.formatIdMap_puid:
            self.formatIdMap_puid[file_format] = self.formatIdCounter_puid
            self.formatIdMap_reverse_puid[self.formatIdCounter_puid] = file_format
            self.formatIdCounter_puid += 1

    def create_csc_matrix_from_dict(self, dictionary, mode):
        """
        Creates a csc- matrix from a dictionary where the
        :param dictionary: dictionary which shall be turned into a csc-matrix
        :param mode: Mode of the program, i.e. does program run use PUID or Wikidata-ID
        :return: csc- matrix
        """
        if mode == Mode.pronom:
            dim = self.formatIdCounter_puid
        else:
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
                else:
                    if data["identifiers"][0]["name"] == "wikidata":
                        mode = Mode.wikidata
                    elif data["identifiers"][0]["name"] == "pronom":
                        mode = Mode.pronom
                    else:
                        print("program can only handle the wikidata and the pronom identifiers")
                        continue

                tmp = []

                # For collecting all the possible formats of a data object
                object_common_formats = set()

                # For collecting all the possible formats of directories in a data object
                directory_common_formats = dict()

                # parsing and sorting of the files
                for x in files:
                    name = x["filename"]
                    possible_formats = x["matches"]
                    formats = set()
                    for y in possible_formats:
                        if y["id"] == 'UNKNOWN':
                            continue
                        if mode == Mode.pronom:
                            self.add_format_id_puid(y["id"])
                            formats.add(self.formatIdMap_puid[y["id"]])
                        else:
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
                        self.add_to_COM(y[0], y[1], MatrixType.global_directory_mat, mode)
                for x in object_format_combinations:
                    for y in x:
                        self.add_to_COM(y[0], y[1], MatrixType.global_mat, mode)

                if mode == Mode.pronom:
                    self.pronom_changed = True
                if mode == Mode.wikidata:
                    self.wiki_changed = True

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

    def save_format_id_map_to_files(self, mode):
        """
        Saves the format ids into a file
        :param mode: Mode of the program, i.e. does program run using PUID or Wikidata-ID
        """
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        if mode == Mode.pronom:
            file = 'format_id_map_puid.json'
            file1 = 'format_id_map_reverse_puid.json'
            with open(os.path.join(path, file), 'w+', encoding='utf8',
                      errors='ignore') as json_file:
                json.dump(self.formatIdMap_puid, json_file)
            with open(os.path.join(path, file1), 'w+', encoding='utf8',
                      errors='ignore') as json_file:
                json.dump(self.formatIdMap_reverse_puid, json_file)
        else:
            file = 'format_id_map.json'
            file1 = 'format_id_map_reverse.json'
            with open(os.path.join(path, file), 'w+', encoding='utf8',
                      errors='ignore') as json_file:
                json.dump(self.formatIdMap, json_file)
            with open(os.path.join(path, file1), 'w+', encoding='utf8',
                      errors='ignore') as json_file:
                json.dump(self.formatIdMap_reverse, json_file)


    def save_normalized_matrix(self, matrix_type, csc_matrix, mode):
        """
        Saves the normalized co-occurrence matrices to a file
        :param matrix_type: Co.occurrence in directory or in object
        :param csc_matrix: matrix to be saved
        :param mode: Mode of the program, i.e. does program run using PUID or Wikidata-ID
        """
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        if matrix_type == MatrixType.global_mat:
            if mode == Mode.pronom:
                file = 'normalized_object_matrix_puid.json'
            else:
                file = 'normalized_object_matrix.json'
        else:
            if mode == Mode.pronom:
                file = 'normalized_directory_matrix_puid.json'
            else:
                file = 'normalized_directory_matrix.json'
        serialize = {}
        tmp = self.build_dictionary_from_csc_matrix(csc_matrix)
        for key, value in tmp.items():
            serialize[str(key)] = value
        with open(os.path.join(path, file), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize, json_file)

    def save_counting_matrices(self, mode):
        """
        Saves the co-occurrence matrix(counting versions) to file
        :param mode: Mode of the program, i.e. does program run using PUID or Wikidata-ID
        """
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        serialize_d = {}
        serialize_o = {}
        if mode == Mode.pronom:
            file = 'counting_matrix_directory_puid.json'
            file1 = 'counting_matrix_object_puid.json'
            for key, value in self.gCOM_puid.items():
                serialize_o[str(key)] = value
            for key, value in self.gdCOM_puid.items():
                serialize_d[str(key)] = value
        else:
            file = 'counting_matrix_directory.json'
            file1 = 'counting_matrix_object.json'
            for key, value in self.gCOM.items():
                serialize_o[str(key)] = value
            for key, value in self.gdCOM.items():
                serialize_d[str(key)] = value

        with open(os.path.join(path, file), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize_d, json_file)
        with open(os.path.join(path, file1), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize_o, json_file)

    def load_format_id_map(self):
        """
        Loads format id map from file
        """
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file = 'format_id_map.json'
        file1 = 'format_id_map_reverse.json'
        with open(os.path.join(path, file), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            self.formatIdMap = data
        with open(os.path.join(path, file1), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                self.formatIdMap_reverse[int(keys)] = value
        max_key = 0
        for keys in self.formatIdMap_reverse:
            # print(keys)
            if keys > max_key:
                max_key = keys
        self.formatIdCounter = max_key + 1

        file2 = 'format_id_map_puid.json'
        file3 = 'format_id_map_reverse_puid.json'
        with open(os.path.join(path, file2), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            self.formatIdMap_puid = data
        with open(os.path.join(path, file3), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                self.formatIdMap_reverse_puid[int(keys)] = value
        max_key = 0
        for keys in self.formatIdMap_reverse_puid:
            # print(keys)
            if keys > max_key:
                max_key = keys
        self.formatIdCounter_puid = max_key + 1

    def load_counting_matrices(self):
        """
        load counting matrices from file
        :return:
        """
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file = 'counting_matrix_directory.json'
        file1 = 'counting_matrix_object.json'
        with open(os.path.join(path, file), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                self.gdCOM[key] = value
        with open(os.path.join(path, file1), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                self.gCOM[key] = value

        file2 = 'counting_matrix_directory_puid.json'
        file3 = 'counting_matrix_object_puid.json'
        with open(os.path.join(path, file2), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                self.gdCOM_puid[key] = value
        with open(os.path.join(path, file3), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                self.gCOM_puid[key] = value

    def pre_process_data_objects_idf(self, path_to_objects):
        """
        Function which processes all the data objects in a given location
        and counts the occurrences of file formats in data objects
        - for the calculation of the idf values of the formats
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
                else:
                    if data["identifiers"][0]["name"] == "wikidata":
                        mode = Mode.wikidata
                    elif data["identifiers"][0]["name"] == "pronom":
                        mode = Mode.pronom
                    else:
                        print("program can only handle the wikidata and the pronom identifiers")
                        continue
                if mode == Mode.pronom:
                    self.number_objects_puid += 1
                else:
                    self.number_objects += 1
                format_set = set()
                format_set_puid = set()
                document_length = 0
                # parsing and sorting of the files
                for x in files:
                    possible_formats = x["matches"]
                    document_length += 1
                    for y in possible_formats:
                        if y["id"] == 'UNKNOWN':
                            continue
                        if mode == Mode.pronom:
                            if y['id'] not in self.formatIdMap_puid:
                                self.add_format_id_puid(y["id"])
                            format_set_puid.add(self.formatIdMap_puid[y['id']])
                        else:
                            if y['id'] not in self.formatIdMap:
                                self.add_format_id(y["id"])
                            format_set.add(self.formatIdMap[y['id']])
                for x in format_set:
                    if x not in self.df_map:
                        self.df_map[x] = 1
                    else:
                        self.df_map[x] += 1
                for y in format_set_puid:
                    if y not in self.df_map_puid:
                        self.df_map_puid[y] = 1
                    else:
                        self.df_map_puid[y] += 1
                if mode == Mode.pronom:
                    self.document_lengths_puid.append(document_length)
                else:
                    self.document_lengths.append(document_length)

    def load_df_maps(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file = 'df_map.json'
        file1 = 'df_map_puid.json'
        file2 = 'lengths.json'
        with open(os.path.join(path, file), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                self.df_map[int(keys)] = value

        with open(os.path.join(path, file1), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data1 = json.load(json_file)
            for keys, value in data1.items():
                self.df_map_puid[int(keys)] = value

        with open(os.path.join(path, file2), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data2 = json.load(json_file)
            self.number_objects = data2['number_objects']
            self.number_objects_puid = data2['number_objects_puid']
            self.document_lengths = data2['document_lengths']
            self.document_lengths_puid = data2['document_lengths_puid']

    def save_df_values(self, mode):
        """
        Saves the values needed for calculation of tf-idf-values
        :param mode: Mode of the program, i.e. does program run using PUID or Wikidata-ID
        """
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        if mode == Mode.pronom:
            file = 'df_map_puid.json'
            with open(os.path.join(path, file), 'w+', encoding='utf8',
                      errors='ignore') as json_file:
                json.dump(self.df_map_puid, json_file)
        else:
            file = 'df_map.json'
            with open(os.path.join(path, file), 'w+', encoding='utf8',
                      errors='ignore') as json_file:
                json.dump(self.df_map, json_file)

        file2 = 'lengths.json'
        serialize = dict()
        serialize['number_objects'] = self.number_objects
        serialize['number_objects_puid'] = self.number_objects_puid
        serialize['document_lengths'] = self.document_lengths
        serialize['document_lengths_puid'] = self.document_lengths_puid
        with open(os.path.join(path, file2), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize, json_file)

    def train_idf_necessary_values(self, path, mode):
        self.load_format_id_map()
        self.load_df_maps()
        self.pre_process_data_objects_idf(path)
        self.save_df_values(mode)


class MatrixType(Enum):
    global_mat = 1
    global_directory_mat = 2
    local_mat = 3
    local_directory_mat = 4


class Mode(Enum):
    wikidata = 1
    pronom = 2


def main(argv):
    otp = ObjectTrainProcessor()
    if len(argv) == 1:
        pass
        # usage()
    else:
        argument_list = argv[1:]
    # Options
    options = "hc:n:"

    # Long options
    long_options = ["help", "continue=", "new="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argument_list, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                pass
                # usage()
            elif currentArgument in ("-c", "--continue"):
                path_to_objects = currentValue
                # loading old data
                otp.load_format_id_map()
                otp.load_counting_matrices()
                otp.load_df_maps()

                # training
                otp.pre_process_data_objects(path_to_objects)
                otp.pre_process_data_objects_idf(path_to_objects)

                # saving new training data
                otp.save_format_id_map_to_files(Mode.wikidata)
                otp.save_format_id_map_to_files(Mode.pronom)
                otp.save_counting_matrices(Mode.wikidata)
                otp.save_counting_matrices(Mode.pronom)
                otp.save_df_values(Mode.pronom)
                otp.save_df_values(Mode.wikidata)

                if otp.wiki_changed:
                    object_matrix = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gCOM, Mode.wikidata))
                    directory_matrix = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gdCOM, Mode.wikidata))
                if otp.pronom_changed:
                    object_matrix_puid = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gCOM_puid, Mode.pronom))
                    directory_matrix_puid = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gdCOM_puid, Mode.pronom))

                if otp.wiki_changed:
                    otp.save_normalized_matrix(MatrixType.global_mat, object_matrix, Mode.wikidata)
                    otp.save_normalized_matrix(MatrixType.global_directory_mat, directory_matrix, Mode.wikidata)
                if otp.pronom_changed:
                    otp.save_normalized_matrix(MatrixType.global_mat, object_matrix_puid, Mode.pronom)
                    otp.save_normalized_matrix(MatrixType.global_directory_mat, directory_matrix_puid, Mode.pronom)

            elif currentArgument in ("-n", "--new"):
                path_to_objects = currentValue

                otp.load_format_id_map()
                otp.pre_process_data_objects(path_to_objects)
                otp.pre_process_data_objects_idf(path_to_objects)

                # saving new training data
                if otp.pronom_changed:
                    otp.save_format_id_map_to_files(Mode.pronom)
                if otp.wiki_changed:
                    otp.save_format_id_map_to_files(Mode.wikidata)

                if otp.pronom_changed:
                    otp.save_counting_matrices(Mode.pronom)
                    otp.save_df_values(Mode.pronom)
                if otp.wiki_changed:
                    otp.save_counting_matrices(Mode.wikidata)
                    otp.save_df_values(Mode.wikidata)

                if otp.wiki_changed:
                    object_matrix = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gCOM, Mode.wikidata))
                    directory_matrix = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gdCOM, Mode.wikidata))
                if otp.pronom_changed:
                    object_matrix_puid = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gCOM_puid, Mode.pronom))
                    directory_matrix_puid = otp.calculate_relative_weight_matrix(otp.create_csc_matrix_from_dict(
                        otp.gdCOM_puid, Mode.pronom))

                if otp.wiki_changed:
                    otp.save_normalized_matrix(MatrixType.global_mat, object_matrix, Mode.wikidata)
                    otp.save_normalized_matrix(MatrixType.global_directory_mat, directory_matrix, Mode.wikidata)
                if otp.pronom_changed:
                    otp.save_normalized_matrix(MatrixType.global_mat, object_matrix_puid, Mode.pronom)
                    otp.save_normalized_matrix(MatrixType.global_directory_mat, directory_matrix_puid, Mode.pronom)

    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))


def usage():
    string = ""
    string += "usage: python3 environment_process.py -h\n"
    string += "                                      -c <Path/to/objects>\n"
    string += "                                      -n <Path/to/objects>\n"
    string += "-h, --help: prints this usage message\n"
    string += "-c, --continue <Path/to/data-objects>: continues training with the data-objects located in\n"
    string += "                                       <Path/to/data-objects>\n"
    string += "-n, --new <Path/to/data-objects>: starts new  training with the data-objects located in\n"
    string += "                                  <Path/to/data-objects>\n"
    print(string)
    sys.exit()


if __name__ == "__main__":
    otp = ObjectTrainProcessor()
    # otp.train_idf_necessary_values(sys.argv[1])
    main(sys.argv)


