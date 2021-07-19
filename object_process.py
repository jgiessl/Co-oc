import scipy.sparse as sp
from sklearn.preprocessing import normalize
import os
import json
from json.decoder import JSONDecodeError
import itertools
from training import MatrixType
from training import Mode


class ObjectProcessor:

    def __init__(self):

        # Map of Wikidata -format ids to Integer-Ids
        self.formatIdMap = {}

        # Map of Integer-Ids to Wikidata -format ids
        self.formatIdMap_reverse = {}

        self.formatIdCounter = 0

        # Stores the number of co-occurrences of the formats in respect to the folders of a Data-object.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.ldCOM = {}  # ldCOM -> local-directory-Co-Occurrence-Matrix

        # Stores the number of co-occurrences of the formats in respect to a Data-object.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.lCOM = {}  # lCOM -> local-Co-Occurrence-Matrix

        # stores the format ids (Integer) of the current data object
        self.formats_of_current_data = set()

        self.formats_of_current_data_puid = set()

        # dictionary for collecting the number of files with known format
        self.stats = {}

        # dictionary for collecting the number of files with known format (PUID)
        self.stats_puid = {}

        # Map of PUIDS to Integer-Ids
        self.formatIdMap_puid = {}

        # Map of Integer-Ids to PUIDs
        self.formatIdMap_reverse_puid = {}

        self.formatIdCounter_puid = 0

        # Stores the number of co-occurrences of the formats in respect to a Data-object.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.lCOM_puid = {}  # lCOM -> local-Co-Occurrence-Matrix

        # Stores the number of co-occurrences of the formats in respect to the folders of a Data-object.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.ldCOM_puid = {}  # ldCOM -> local-directory-Co-Occurrence-Matrix

    def add_to_COM(self, id_1, id_2, matrix_type, mode):
        """
        Helper function for building the matrices which store the frequencies of the format co-occurrences
        :param id_1: Id of the first format of the combination
        :param id_2: Id of the second format of the combination
        :param matrix_type: gives the type of the reference matrix, i.e.
                            MatrixType.local_directory_mat : Stores the co-occurrences of formats in the directories
                                                             of the current data-object
                            MatrixType.local_mat : Stores the co-occurrences of formats of the current data-object
        :param mode: Mode of the program, i.e. does program run use PUID or Wikidata-ID
        """
        if matrix_type == MatrixType.local_directory_mat:
            if mode == Mode.pronom:
                reference_matrix = self.ldCOM_puid
            else:
                reference_matrix = self.ldCOM
        else:
            if mode == Mode.pronom:
                reference_matrix = self.lCOM_puid
            else:
                reference_matrix = self.lCOM
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
        :param file_format: Wikidata ID of the file format
        """
        if file_format not in self.formatIdMap:
            self.formatIdMap[file_format] = self.formatIdCounter
            self.formatIdMap_reverse[self.formatIdCounter] = file_format
            self.formatIdCounter += 1


    def add_format_id_puid(self, file_format):
        """
        Adds file format to an index map
        :param file_format: PUID of the file format
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

    def create_diagonal_matrix(self, mode):
        """
        Creates a diagonal matrix which only has 1 on the positions of the formats it contains
        :return: matrix in csc_matrix format
        """
        if mode == Mode.wikidata:
            dim = self.formatIdCounter
            s = self.formats_of_current_data
        else:
            dim = self.formatIdCounter_puid
            s = self.formats_of_current_data_puid
        rows, cols, vals = [], [], []
        for x in s:
            rows.append(x)
            cols.append(x)
            vals.append(1)
        x = sp.csc_matrix((vals, (rows, cols)), shape=(dim, dim))
        return x

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

    def partial_add(self, l_mat, g_mat, mode):
        """
        Function which sums two matrices by summing only the entries where
        both matrices are not zero
        :param l_mat: Matrix describing a given data object
        :param g_mat: Matrix describing all data objects in the corpus (formatted as coo-dictionary)
        :param mode: Mode of the program, i.e. does the program run use PUID or Wikidata-ID
        :return: The summation matrix in csc format
        """
        if mode == Mode.wikidata:
            dim = self.formatIdCounter
        else:
            dim = self.formatIdCounter_puid
        x = l_mat.tocoo()
        X = list(zip(x.row, x.col, x.data))
        rows = []
        cols = []
        data = []
        for i in X:
            rows.append(i[0])
            cols.append(i[1])
            if (i[0], i[1]) in g_mat:
                data.append(i[2] + g_mat[(i[0], i[1])])
            else:
                data.append(i[2])
        return sp.csc_matrix((data, (rows, cols)), shape=(dim, dim))

    def process_data_object(self, path, filename):
        """
        Function which processes a specific data object and builds the matrix
        representing the format co-occurrences of the object
        :param path: Path/To/Objects
        :param filename: Name of the Object
        """
        with open(os.path.join(path, filename), 'r', encoding='utf8',
                  errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                return
            files = data["files"]
            if len(files) == 0:
                return

            if len(data["identifiers"]) > 1:
                print("program currently cannot handle multiple identifiers at the same time.")
                return
            elif len(data["identifiers"]) < 1:
                print("no identifiers are specified in siegfried output.")
                return
            else:
                if data["identifiers"][0]["name"] == "wikidata":
                    mode = Mode.wikidata
                elif data["identifiers"][0]["name"] == "pronom":
                    mode = Mode.pronom
                else:
                    print("program can only handle the wikidata and the pronom identifiers")
                    return
            tmp = []

            # For collecting all the possible formats of a data object
            object_common_formats = set()

            # For collecting all the possible formats of directories in a data object
            directory_common_formats = dict()

            # Counters for calculating the share of the determinable formats
            file_counter = 0
            unknown_counter = 0
            distinct_formats = set()

            # parsing and sorting of the files
            for x in files:
                name = x["filename"]
                possible_formats = x["matches"]
                formats = set()
                file_counter += 1
                for y in possible_formats:
                    if y["id"] == 'UNKNOWN':
                        unknown_counter += 1
                        continue
                    if mode == Mode.pronom:
                        if y['id'] not in self.formatIdMap_puid:
                            self.add_format_id_puid(y["id"])
                        formats.add(self.formatIdMap_puid[y["id"]])
                        distinct_formats.add((y['id'], y['format']))

                        # collect format id for current data object
                        self.formats_of_current_data_puid.add(self.formatIdMap_puid[y['id']])
                    else:
                        if y['id'] not in self.formatIdMap:
                            self.add_format_id(y["id"])
                        formats.add(self.formatIdMap[y["id"]])
                        distinct_formats.add((y['id'], y['format']))

                        # collect format id for current data object
                        self.formats_of_current_data.add(self.formatIdMap[y['id']])

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

            # adding statistics
            if mode == Mode.pronom:
                temp_list = []
                for x in distinct_formats:
                    temp_list.append([x[0], x[1]])
                self.stats_puid[filename] = [file_counter, unknown_counter, temp_list]
            else:
                temp_list = []
                for x in distinct_formats:
                    temp_list.append([x[0], x[1]])
                self.stats[filename] = [file_counter, unknown_counter, temp_list]
            # adding the co-occurrences the the matrices
            for x in directory_format_combinations:
                for y in x:
                    self.add_to_COM(y[0], y[1], MatrixType.local_directory_mat, mode)
            for x in object_format_combinations:
                for y in x:
                    self.add_to_COM(y[0], y[1], MatrixType.local_mat, mode)

    def process_data_object_tf(self, path, filename):
        """
        Function which processes a specific data object and builds the matrix
        representing the format co-occurrences of the object
        :param path: Path/To/Objects
        :param filename: Name of the Object
        """
        with open(os.path.join(path, filename), 'r', encoding='utf8',
                  errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                return
            files = data["files"]
            if len(files) == 0:
                return

            if len(data["identifiers"]) > 1:
                print("program currently cannot handle multiple identifiers at the same time.")
                return
            elif len(data["identifiers"]) < 1:
                print("no identifiers are specified in siegfried output.")
                return
            else:
                if data["identifiers"][0]["name"] == "wikidata":
                    mode = Mode.wikidata
                elif data["identifiers"][0]["name"] == "pronom":
                    mode = Mode.pronom
                else:
                    print("program can only handle the wikidata and the pronom identifiers")
                    return

            tf_map = {}
            tf_map_puid = {}
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
                        if self.formatIdMap_puid[y['id']] not in tf_map_puid:
                            tf_map_puid[self.formatIdMap_puid[y['id']]] = 1
                        else:
                            tf_map_puid[self.formatIdMap_puid[y['id']]] += 1
                    else:
                        if y['id'] not in self.formatIdMap:
                            self.add_format_id(y["id"])
                        if self.formatIdMap[y['id']] not in tf_map:
                            tf_map[self.formatIdMap[y['id']]] = 1
                        else:
                            tf_map[self.formatIdMap[y['id']]] += 1
        return tf_map, tf_map_puid, document_length








