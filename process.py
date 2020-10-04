import scipy.sparse as sp
from sklearn.preprocessing import normalize
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import json
from json.decoder import JSONDecodeError
import itertools
from math import log2
from enum import Enum


class ObjectProcessor:

    def __init__(self, stat_collector):
        # Object for collecting statistics
        self.stats = stat_collector

        # Map of PUID -format ids to Integer-Ids
        self.formatIdMap = {}

        # Map of Integer-Ids to PUID -format ids
        self.formatIdMap_reverse = {}

        # synchronize format-ids for the stats collector
        self.stats.formatIdMap = self.formatIdMap
        self.stats.formatIdMap_reverse = self.stats.formatIdMap_reverse

        self.formatIdCounter = 0

        # Stores the number of co-occurrences of the formats in respect to the Data-objects.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.gCOM = {}  # gCOM -> global-Co-Occurrence-Matrix

        # Stores the number of co-occurrences of the formats in respect to the folders of a Data-object.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.ldCOM = {}  # ldCOM -> local-directory-Co-Occurrence-Matrix

        # Stores the number of co-occurrences of the formats in respect to the folders of all Data-objects.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.gdCOM = {}  # gdCOM -> global-directory-Co-Occurrence-Matrix

        # Stores the number of co-occurrences of the formats in respect to a Data-object.
        # Dictionary which uses tuples of Integer-Ids(formats) as keys and
        # the number of co-occurrences as values.
        self.lCOM = {}  # lCOM -> local-Co-Occurrence-Matrix

        # Document/data-objects count for the calculation of idf score
        self.doc_count = 0

        # idf_map -> maps for each format the number of documents/data-objects which contain the format
        self.idf_map = {}

        # Average document length (number of files in a data-object)
        self.avdl = 0

        # stores the format ids (Integer) of the current data object
        self.formats_of_current_data = set()

    def add_to_COM(self, id_1, id_2, matrix_type):
        """
        Helper function for building the matrices which store the frequencies of the format co-occurrences
        :param id_1: Id of the first format of the combination
        :param id_2: Id of the second format of the combination
        :param matrix_type: gives the type of the reference matrix, i.e.
                            MatrixType.local_directory_mat : Stores the co-occurrences of formats in the directories
                                                             of the current data-object
                            MatrixType.local_mat : Stores the co-occurrences of formats of the current data-object
                            MatrixType.global_directory_mat : Stores the co-occurrences of formats in the directories
                                                             of all the data-object
                            MatrixType.global_mat : Stores the co-occurrences of formats in
                                                              all the data-object
        """
        if matrix_type == MatrixType.local_directory_mat:
            reference_matrix = self.ldCOM
        elif matrix_type == MatrixType.global_directory_mat:
            reference_matrix = self.gdCOM
        elif matrix_type == MatrixType.global_mat:
            reference_matrix = self.gCOM
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
        :param file_format: PUID of the file
        """
        if file_format not in self.formatIdMap:
            self.formatIdMap[file_format] = self.formatIdCounter
            self.formatIdMap_reverse[self.formatIdCounter] = file_format
            self.formatIdCounter += 1

    def create_csc_matrix_from_dict(self, dictionary):
        """
        Creates a csc- matrix from a dictionary where the
        :param dictionary: dictionary which shall be
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
        # y = sp.tril(x)
        # return y / 2
        return x / 2

    @staticmethod
    def get_directory(filepath, filename):
        """
        Gets the directory of the data object which contains the given file
        :param filepath: Path/To/the/File/In/Object
        :param filename: Name of the File
        :return: Directory of file in a data object
        """
        # sep = os.sep
        tmp = filepath.split("/")
        while tmp[0] != filename:
            del tmp[0]
        del tmp[0]
        if len(tmp) == 1:
            return 'root'
        else:
            del tmp[-1]
            return "/".join(tmp)

    def create_diagonal_matrix(self):
        """
        Creates a diagonal matrix which only has 1 on the positions of the formats it contains
        :return: matrix in csc_matrix format
        """
        dim = self.formatIdCounter
        s = self.formats_of_current_data
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

    def partial_add(self, l_mat, g_mat):
        """
        Function which sums two matrices by summing only the entries where
        both matrices are not zero
        :param l_mat: Matrix describing a given data object
        :param g_mat: Matrix describing all data objects in the corpus
        :return: The summation matrix in csc format
        """
        dim = self.formatIdCounter
        x = l_mat.tocoo()
        y = g_mat.tocoo()
        X = list(zip(x.row, x.col, x.data))
        Y = list(zip(y.row, y.col, y.data))
        rows = []
        cols = []
        data = []
        for i in X:
            for j in Y:
                if i[0] == j[0] and i[1] == j[1]:
                    rows.append(i[0])
                    cols.append(i[1])
                    data.append(i[2] + j[2])
                    break
        return sp.csc_matrix((data, (rows, cols)), shape=(dim, dim))

    def pre_process_data_objects(self, path_to_objects, q):
        """
        Function which processes all the data objects in a given location
        and builds the matrix representing the format co-occurrences of the object corpus
        :param path_to_objects: Path/To/Objects
        :param q: queue for communicating with the GUI- thread
        """
        for filename in os.listdir(path_to_objects):
            with open(os.path.join(path_to_objects, filename), 'r', encoding='utf8',
                      errors='ignore') as f:
                try:
                    data = json.load(f)
                except JSONDecodeError:
                    q.put('### Could not decode Jason {0}'.format(filename))
                    continue
                files = data["files"]
                if len(files) == 0:
                    q.put("### Siegfried-output of {0} doesn't have any files".format(filename))
                    continue
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
                    file_counter += 1
                    name = x["filename"]
                    possible_formats = x["matches"]
                    formats = set()
                    for y in possible_formats:
                        if y["id"] == 'UNKNOWN':
                            unknown_counter += 1
                            continue
                        self.add_format_id(y["id"])
                        distinct_formats.add(y['id'])
                        formats.add(self.formatIdMap[y["id"]])
                    directory = self.get_directory(name, filename)
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
                self.stats.stats[filename] = [file_counter, unknown_counter, distinct_formats]
                # adding the co-occurrences the the matrices
                for x in directory_format_combinations:
                    for y in x:
                        self.add_to_COM(y[0], y[1], MatrixType.global_directory_mat)
                for x in object_format_combinations:
                    for y in x:
                        self.add_to_COM(y[0], y[1], MatrixType.global_mat)

        # formatting and writing of the log messages
                q.put("{0}: For {1} out of {2} files".format(filename, unknown_counter, file_counter)
                      + " the PUID could not be determined")

        # giving format ids to the stat-collector
        self.stats.formatIdMap = self.formatIdMap
        self.stats.formatIdMap_reverse = self.formatIdMap_reverse

    def pre_process_idf(self, path_to_objects):
        """
        Calculates the idf values for all the formats in the corpus
        :param path_to_objects: Path/To/Objects
        """
        for filename in os.listdir(path_to_objects):
            with open(os.path.join(path_to_objects, filename), 'r', encoding='utf8',
                      errors='ignore') as f:
                try:
                    data = json.load(f)
                except JSONDecodeError:
                    continue
                files = data["files"]
                if len(files) == 0:
                    continue
                self.doc_count += 1
                file_counter = 0
                already_counted = set()
                for x in files:
                    file_counter += 1
                    possible_formats = x["matches"]
                    for y in possible_formats:
                        if y["id"] == 'UNKNOWN':
                            continue
                        if y["id"] not in self.idf_map:
                            self.idf_map[self.formatIdMap[y["id"]]] = 1
                            already_counted.add(y["id"])
                        else:
                            if y["id"] not in already_counted:
                                self.idf_map[self.formatIdMap[y["id"]]] += 1
                self.avdl += file_counter
        self.avdl = self.avdl / self.doc_count
        for key in self.idf_map:
            self.idf_map[key] = log2(self.doc_count / self.idf_map[key])

    def process_tf(self, path, filename):
        """
        Extracts the format frequencies of the data object
        :param path: Path/To/Object
        :param filename: Name of the data object
        :return: (Number of files in the Object , term frequency of each format)
        """
        # number of files for each format
        tf_map = {}
        # number of files in the data object
        file_counter = 0
        with open(os.path.join(path, filename), 'r', encoding='utf8',
                  errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                return
            files = data["files"]
            if len(files) == 0:
                return
            for x in files:
                file_counter += 1
                possible_formats = x["matches"]
                for y in possible_formats:
                    if y["id"] == 'UNKNOWN':
                        continue
                    if y["id"] not in tf_map:
                        tf_map[self.formatIdMap[y["id"]]] = 1
                    else:
                        tf_map[self.formatIdMap[y["id"]]] += 1
            return file_counter, tf_map

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
                    self.add_format_id(y["id"])
                    formats.add(self.formatIdMap[y["id"]])

                    # collect format id for current data object
                    self.formats_of_current_data.add(self.formatIdMap[y['id']])

                directory = self.get_directory(name, filename)
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
                    self.add_to_COM(y[0], y[1], MatrixType.local_directory_mat)
            for x in object_format_combinations:
                for y in x:
                    self.add_to_COM(y[0], y[1], MatrixType.local_mat)


class EnvironmentProcessor:

    def __init__(self):
        # Maps environments to Integer-Ids
        self.environmentIdMap = {}
        # Maps Integer-Ids to environment names
        self.environmentIdMap_reverse = {}

        self.idCounter = 0

        # Maps environment Ids to  readable formats (PUID)
        self.readable_formats_of_environment = {}

    def add_environment(self, name):
        """
        Adds an environment Id
        :param name: Name of the environment
        """
        if name not in self.environmentIdMap:
            self.environmentIdMap[name] = self.idCounter
            self.environmentIdMap_reverse[self.idCounter] = name
            self.idCounter += 1

    def pre_process_environments(self, path, formatIdMap):
        """
        Processes the environments gets the the readable file formats of each environment
        according to WikiData
        :param path: Path/To/Environments-file-folder
        :param formatIdMap: Map which holds an integer Id for each format of the data object corpus
        """
        for filename in os.listdir(path):
            with open(os.path.join(path, filename), 'r', encoding='utf8',
                      errors='ignore') as f:
                try:
                    data = json.load(f)
                except JSONDecodeError:
                    print('Could not decode environment file {0}'.format(filename))
                env = data
                self.add_environment(env["name"])
                readable_formats = set()
                for x in env["programs"]:
                    tmp = self.get_readable_formats_of_program(x, formatIdMap)
                    readable_formats = readable_formats.union(tmp)
                    if self.environmentIdMap[env["name"]] not in self.readable_formats_of_environment:
                        self.readable_formats_of_environment[self.environmentIdMap[env["name"]]] = readable_formats
                    else:
                        uni = self.readable_formats_of_environment[self.environmentIdMap[env["name"]]].\
                            union(readable_formats)
                        self.readable_formats_of_environment[self.environmentIdMap[env["name"]]] = uni

    def write_readable_formats_to_file(self, formatIdmap_rverse):
        """
        Writes the the readable formats for an environment into a save file
        """
        path = os.path.dirname(os.path.abspath(__file__))
        serialize = {}
        for key in self.readable_formats_of_environment:
            formats = []
            tmp = list(self.readable_formats_of_environment[key])
            for x in tmp:
                formats.append(formatIdmap_rverse[x])
            serialize[self.environmentIdMap_reverse[key]] = [formats, key]
        with open(os.path.join(path, "environments_save.json"), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize, json_file)

    def read_readable_formats_from_file(self, formatIdmap):
        """
        Gets the readable formats for the environments from a save file
        """
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, 'environments_save.json'), 'r', encoding='utf8',
                  errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                return
            for x in data:
                self.environmentIdMap[x] = data[x][1]
                self.environmentIdMap_reverse[data[x][1]] = x
                format_ids = set()
                for y in data[x][0]:
                    format_ids.add(formatIdmap[y])
                self.readable_formats_of_environment[data[x][1]] = format_ids

    def get_readable_formats_of_program(self, programWDID, formatIdMap):
        """
        Function which gets all the readable for a given programm according to WikiData
        :param programWDID: WikiData ID for a program
        :param formatIdMap: Map which holds an integer Id for each format of the data object corpus
        :return: All the readable formats of a program as specified in WikiData
        """
        endpoint_url = "https://query.wikidata.org/sparql"
        query = """SELECT ?item
        WHERE
         {
         wd:%s wdt:P1072 ?format .
          ?format wdt:P2748 ?item
         }""" % programWDID

        results = self.get_results(endpoint_url, query)
        formats = set()
        for result in results["results"]["bindings"]:
            x = result["item"]["value"]
            formats.add(x)
        res = set()
        for x in list(formats):
            if x not in formatIdMap:
                continue
            else:
                res.add(formatIdMap[x])
        return res

    def get_results(self, endpoint_url, query):
        """
        Query helper for WikiData
        :param endpoint_url: link to WikiData query page
        :param query: Query to be answered by WikiData
        :return: Query result
        """
        user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
        sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()


class MatrixType(Enum):
    local_mat = 1
    local_directory_mat = 2
    global_mat = 3
    global_directory_mat = 4


