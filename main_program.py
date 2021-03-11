from object_process import *
from matcher import *
import json
from environment_process import *
from ast import literal_eval as mt
import time
import multiprocessing as mp
from training import Mode


class Calculator:

    def __init__(self):
        self.op = ObjectProcessor()

        self.readable_formats_of_environment = {}
        # Map of Wikidata -format ids to Integer-Ids
        self.formatIdMap = {}

        # Map of Integer-Ids to Wikidata -format ids
        self.formatIdMap_reverse = {}

        self.formatIdCounter = 0

        self.environmentIdMap = {}

        self.environmentIdMap_reverse = {}

        self.global_co_occurrence_matrix = {}

        self.global_co_occurrence_matrix_dir = {}

        self.g = 0

        self.gdir = 0

        self.l = 0

        self.ldir = 0

        self.offset = 0

        self.matcher = Matcher()

        # new
        self.readable_formats_of_environment_puid = {}

        self.formatIdMap_puid = {}
        self.formatIdMap_reverse_puid = {}
        self.formatIdCounter_puid = 0
        self.global_co_occurrence_matrix_puid = {}
        self.global_co_occurrence_matrix_dir_puid = {}

    def load_format_id_map(self):
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

    def load_format_id_map_puid(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file = 'format_id_map_puid.json'
        file1 = 'format_id_map_reverse_puid.json'
        with open(os.path.join(path, file), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            # self.formatIdMap = data
            self.formatIdMap_puid = data
        with open(os.path.join(path, file1), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                self.formatIdMap_reverse_puid[int(keys)] = value
                # self.formatIdMap_reverse[int(keys)] = value
        max_key = 0
        # for keys in self.formatIdMap_reverse:
        for keys in self.formatIdMap_reverse_puid:
            # print(keys)
            if keys > max_key:
                max_key = keys
        # self.formatIdCounter = max_key + 1
        self.formatIdCounter_puid = max_key + 1

    def load_environment_id_map(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'environment_data'
        file = 'environment_id_map.json'
        file1 = 'environment_id_map_reverse.json'
        if file not in os.listdir(path):
            print("There are currently no environments saved - starting anew")
            return
        with open(os.path.join(path, file), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            self.environmentIdMap = data
        with open(os.path.join(path, file1), 'r+', encoding='utf8',
                  errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                self.environmentIdMap_reverse[int(keys)] = value

    def read_readable_formats_from_file(self, formatIdmap):
        """
        Gets the readable formats for the environments from a save file
        """
        path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'data' + os.sep + 'environment_data'
        if 'environments_save.json' not in os.listdir(path):
            print('currently there are no environments known o the program')
            return
        with open(os.path.join(path, 'environments_save.json'), 'r', encoding='utf8',
                  errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                return
            if len(data) == 0:
                print('currently there are no environments known o the program')
                return
            for x in data:
                self.environmentIdMap[x] = data[x][1]
                self.environmentIdMap_reverse[data[x][1]] = x
                format_ids = set()
                for y in data[x][0]:
                    format_ids.add(formatIdmap[y])
                self.readable_formats_of_environment[data[x][1]] = format_ids

    def read_readable_formats_from_file_puid(self, formatIdmap_puid):
        """
        Gets the readable formats for the environments from a save file
        """
        path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'data' + os.sep + 'environment_data'
        if 'environments_save_puid.json' not in os.listdir(path):
            print('currently there are no environments known o the program')
            return
        with open(os.path.join(path, 'environments_save_puid.json'), 'r', encoding='utf8',
                  errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                return
            if len(data) == 0:
                print('currently there are no environments known o the program')
                return
            for x in data:
                self.environmentIdMap[x] = data[x][1]
                self.environmentIdMap_reverse[data[x][1]] = x
                format_ids = set()
                for y in data[x][0]:
                    format_ids.add(formatIdmap_puid[y])
                # self.readable_formats_of_environment[data[x][1]] = format_ids
                self.readable_formats_of_environment_puid[data[x][1]] = format_ids

    def load_normalized_matrices(self):
        if os.cpu_count() >= 3:
            p1 = mp.Process(target=self.process_target_directory_matrix)
            p2 = mp.Process(target=self.process_target_object_matrix)
            p2.start()
            p1.start()
            # print(mp.active_children())
            p1.join()
            p2.join()
        else:
            sep = os.sep
            path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
            file = 'normalized_directory_matrix.json'
            file1 = 'normalized_object_matrix.json'
            with open(os.path.join(path, file), 'r+', encoding='utf8', errors='ignore') as json_file:
                data = json.load(json_file)
                for keys, value in data.items():
                    key = mt(keys)
                    self.global_co_occurrence_matrix_dir[key] = value
            with open(os.path.join(path, file1), 'r+', encoding='utf8', errors='ignore') as json_file:
                data = json.load(json_file)
                for keys, value in data.items():
                    key = mt(keys)
                    self.global_co_occurrence_matrix[key] = value

    def load_normalized_matrices_puid(self):
        if os.cpu_count() >= 3:
            p1 = mp.Process(target=self.process_target_directory_matrix_puid)
            p2 = mp.Process(target=self.process_target_object_matrix_puid)
            p2.start()
            p1.start()
            # print(mp.active_children())
            p1.join()
            p2.join()
        else:
            sep = os.sep
            path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
            file = 'normalized_directory_matrix_puid.json'
            file1 = 'normalized_object_matrix_puid.json'
            with open(os.path.join(path, file), 'r+', encoding='utf8', errors='ignore') as json_file:
                data = json.load(json_file)
                for keys, value in data.items():
                    key = mt(keys)
                    # self.global_co_occurrence_matrix_dir[key] = value
                    self.global_co_occurrence_matrix_dir_puid[key] = value
            with open(os.path.join(path, file1), 'r+', encoding='utf8', errors='ignore') as json_file:
                data = json.load(json_file)
                for keys, value in data.items():
                    key = mt(keys)
                    # self.global_co_occurrence_matrix[key] = value
                    self.global_co_occurrence_matrix_puid[key] = value

    def process_target_directory_matrix(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file = 'normalized_directory_matrix.json'
        with open(os.path.join(path, file), 'r+', encoding='utf8', errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                self.global_co_occurrence_matrix_dir[key] = value

    def process_target_directory_matrix_puid(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file = 'normalized_directory_matrix_puid.json'
        with open(os.path.join(path, file), 'r+', encoding='utf8', errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                # self.global_co_occurrence_matrix_dir[key] = value
                self.global_co_occurrence_matrix_dir_puid[key] = value

    def process_target_object_matrix(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file1 = 'normalized_object_matrix.json'
        with open(os.path.join(path, file1), 'r+', encoding='utf8', errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                self.global_co_occurrence_matrix[key] = value

    def process_target_object_matrix_puid(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'training_data'
        file1 = 'normalized_object_matrix_puid.json'
        with open(os.path.join(path, file1), 'r+', encoding='utf8', errors='ignore') as json_file:
            data = json.load(json_file)
            for keys, value in data.items():
                key = mt(keys)
                # self.global_co_occurrence_matrix[key] = value
                self.global_co_occurrence_matrix_puid[key] = value

    def setup(self, mode):
        sep = os.sep
        data = self.get_parameters(os.path.dirname(os.path.abspath(__file__)) + sep + 'data', "config.json")
        self.g = data["global"]
        self.gdir = data["global_dir"]
        self.l = data["local"]
        self.ldir = data["local_dir"]
        self.offset = data["offset"]
        if mode == Mode.pronom:
            self.load_format_id_map_puid()
            self.op.formatIdMap_puid = self.formatIdMap_puid
            self.op.formatIdMap_reverse_puid = self.formatIdMap_reverse_puid
            self.op.formatIdCounter_puid = self.formatIdCounter_puid
            self.load_environment_id_map()
            self.read_readable_formats_from_file_puid(self.formatIdMap_puid)
            self.load_normalized_matrices_puid()
            self.matcher.readable_formats_of_environment_puid = self.readable_formats_of_environment_puid
        else:
            self.load_format_id_map()
            self.op.formatIdMap = self.formatIdMap
            self.op.formatIdMap_reverse = self.formatIdMap_reverse
            self.op.formatIdCounter = self.formatIdCounter
            self.load_environment_id_map()
            self.read_readable_formats_from_file(self.formatIdMap)
            self.load_normalized_matrices()
            self.matcher.readable_formats_of_environment = self.readable_formats_of_environment

    def setup_complete(self):
        sep = os.sep
        data = self.get_parameters(os.path.dirname(os.path.abspath(__file__)) + sep + 'data', "config.json")
        self.g = data["global"]
        self.gdir = data["global_dir"]
        self.l = data["local"]
        self.ldir = data["local_dir"]
        self.offset = data["offset"]

        self.load_format_id_map_puid()
        self.load_format_id_map()

        self.op.formatIdMap_puid = self.formatIdMap_puid
        self.op.formatIdMap_reverse_puid = self.formatIdMap_reverse_puid
        self.op.formatIdCounter_puid = self.formatIdCounter_puid

        self.op.formatIdMap = self.formatIdMap
        self.op.formatIdMap_reverse = self.formatIdMap_reverse
        self.op.formatIdCounter = self.formatIdCounter

        self.load_environment_id_map()

        self.read_readable_formats_from_file_puid(self.formatIdMap_puid)
        self.read_readable_formats_from_file(self.formatIdMap)

        self.load_normalized_matrices_puid()
        self.load_normalized_matrices()

        self.matcher.readable_formats_of_environment_puid = self.readable_formats_of_environment_puid
        self.matcher.readable_formats_of_environment = self.readable_formats_of_environment

    def calculate(self, path_to_object, filename, mode):

        # summing the bias matrices
        if mode == Mode.pronom:
            global_co_occurrence_matrix_csc_puid = self.op.create_csc_matrix_from_dict(
                self.global_co_occurrence_matrix_puid, mode)
            global_co_occurrence_matrix_dir_csc_puid = self.op.create_csc_matrix_from_dict(
                self.global_co_occurrence_matrix_dir_puid, mode)
            processed_matrix =\
                self.g * global_co_occurrence_matrix_csc_puid + self.gdir * global_co_occurrence_matrix_dir_csc_puid
        else:
            global_co_occurrence_matrix_csc = self.op.create_csc_matrix_from_dict(self.global_co_occurrence_matrix,
                                                                                  mode)
            global_co_occurrence_matrix_dir_csc = self.op.create_csc_matrix_from_dict(
                self.global_co_occurrence_matrix_dir, mode)
            processed_matrix =\
                self.g * global_co_occurrence_matrix_csc + self.gdir * global_co_occurrence_matrix_dir_csc


        # formatting matrix for partial addition
        p_m_coo = processed_matrix.tocoo()
        pmf = list(zip(p_m_coo.row, p_m_coo.col, p_m_coo.data))
        processed_matrix_formatted = dict()
        for x in pmf:
            processed_matrix_formatted[(x[0], x[1])] = x[2]


        # here calc start
        self.op.process_data_object(path_to_object, filename)

        if mode == Mode.pronom:
            # summing matrices describing the current data-object
            matrix = self.ldir * self.op.calculate_relative_weight_matrix(self.op.create_csc_matrix_from_dict(
                self.op.ldCOM_puid, mode)) + self.l * self.op.calculate_relative_weight_matrix(
                self.op.create_csc_matrix_from_dict(self.op.lCOM_puid, mode))
            off = self.op.create_diagonal_matrix(mode)
            # summing the bias matrices and the matrices describing the current data-object
            mat = self.op.partial_add(matrix, processed_matrix_formatted, mode) + self.offset * off
        else:
            # summing matrices describing the current data-object
            matrix = self.ldir * self.op.calculate_relative_weight_matrix(self.op.create_csc_matrix_from_dict(
                self.op.ldCOM, mode)) + self.l * self.op.calculate_relative_weight_matrix(
                self.op.create_csc_matrix_from_dict(self.op.lCOM, mode))
            off = self.op.create_diagonal_matrix(mode)
            # summing the bias matrices and the matrices describing the current data-object
            mat = self.op.partial_add(matrix, processed_matrix_formatted, mode) + self.offset * off


        # make rankings
        if mode == Mode.pronom:
            result = self.matcher.rank_environments_for_object_puid(mat, self.environmentIdMap)
            # getting additoinal information and formatting the output
            number_files = self.op.stats_puid[filename][0]
            number_unknown_files = self.op.stats_puid[filename][1]
            formats = list(self.op.stats_puid[filename][2])
            allknown = self.matcher.check_for_all_known_formats_puid(off, self.environmentIdMap)
            res = self.format_result(filename, number_files, number_unknown_files, formats, result, allknown)
        else:
            result = self.matcher.rank_environments_for_object(mat, self.environmentIdMap)
            # getting additoinal information and formatting the output
            number_files = self.op.stats[filename][0]
            number_unknown_files = self.op.stats[filename][1]
            formats = list(self.op.stats[filename][2])
            allknown = self.matcher.check_for_all_known_formats(off, self.environmentIdMap)
            res = self.format_result(filename, number_files, number_unknown_files, formats, result, allknown)

        dumping_results(res)
        # reset local storage
        self.op.lCOM.clear()
        self.op.ldCOM.clear()
        self.op.ldCOM_puid.clear()
        self.op.lCOM_puid.clear()
        self.op.stats.clear()
        self.op.stats_puid.clear()
        if mode == Mode.pronom:
            self.op.formats_of_current_data_puid.clear()
        else:
            self.op.formats_of_current_data.clear()

    def calculate_whole_folder(self, path_to_object):
        # summing the bias matrices
        global_co_occurrence_matrix_csc = self.op.create_csc_matrix_from_dict(self.global_co_occurrence_matrix,
                                                                              Mode.wikidata)
        global_co_occurrence_matrix_dir_csc = self.op.create_csc_matrix_from_dict(
            self.global_co_occurrence_matrix_dir, Mode.wikidata)
        processed_matrix = self.g * global_co_occurrence_matrix_csc + self.gdir * global_co_occurrence_matrix_dir_csc

        # formatting matrix for partial addition
        p_m_coo = processed_matrix.tocoo()
        pmf = list(zip(p_m_coo.row, p_m_coo.col, p_m_coo.data))
        processed_matrix_formatted = dict()
        for x in pmf:
            processed_matrix_formatted[(x[0], x[1])] = x[2]

        global_co_occurrence_matrix_csc_puid = self.op.create_csc_matrix_from_dict(
            self.global_co_occurrence_matrix_puid, Mode.pronom)
        global_co_occurrence_matrix_dir_puid = self.op.create_csc_matrix_from_dict(
            self.global_co_occurrence_matrix_dir_puid, Mode.pronom)
        processed_matrix_puid =\
            self.g * global_co_occurrence_matrix_csc_puid + self.gdir * global_co_occurrence_matrix_dir_puid

        # formatting matrix for partial addition
        p_m_coo_puid = processed_matrix_puid.tocoo()
        pmf_puid = list(zip(p_m_coo_puid.row, p_m_coo_puid.col, p_m_coo_puid.data))
        processed_matrix_formatted_puid = dict()
        for x in pmf_puid:
            processed_matrix_formatted_puid[(x[0], x[1])] = x[2]

        for filename in os.listdir(path_to_object):
            mode = check_mode(path_to_object, filename)
            if mode is None:
                continue
            self.op.process_data_object(path_to_object, filename)

            if mode == Mode.wikidata:
                # summing matrices describing the current data-object
                matrix = self.ldir * self.op.calculate_relative_weight_matrix(self.op.create_csc_matrix_from_dict(
                    self.op.ldCOM, mode)) + self.l * self.op.calculate_relative_weight_matrix(
                    self.op.create_csc_matrix_from_dict(self.op.lCOM, mode))
                off = self.op.create_diagonal_matrix(mode)
                # summing the bias matrices and the matrices describing the current data-object
                mat = self.op.partial_add(matrix, processed_matrix_formatted, mode) + self.offset * off
            else:
                # summing matrices describing the current data-object
                matrix = self.ldir * self.op.calculate_relative_weight_matrix(self.op.create_csc_matrix_from_dict(
                    self.op.ldCOM_puid, mode)) + self.l * self.op.calculate_relative_weight_matrix(
                    self.op.create_csc_matrix_from_dict(self.op.lCOM_puid, mode))
                off = self.op.create_diagonal_matrix(mode)
                # summing the bias matrices and the matrices describing the current data-object
                mat = self.op.partial_add(matrix, processed_matrix_formatted_puid, mode) + self.offset * off

            # make rankings
            if mode == Mode.pronom:
                result = self.matcher.rank_environments_for_object_puid(mat, self.environmentIdMap)
                # getting additional information and formatting the output
                number_files = self.op.stats_puid[filename][0]
                number_unknown_files = self.op.stats_puid[filename][1]
                formats = list(self.op.stats_puid[filename][2])
                allknown = self.matcher.check_for_all_known_formats_puid(off, self.environmentIdMap)
                res = self.format_result(filename, number_files, number_unknown_files, formats, result, allknown)
            else:
                result = self.matcher.rank_environments_for_object(mat, self.environmentIdMap)
                # getting additoinal information and formatting the output
                number_files = self.op.stats[filename][0]
                number_unknown_files = self.op.stats[filename][1]
                formats = list(self.op.stats[filename][2])
                allknown = self.matcher.check_for_all_known_formats(off, self.environmentIdMap)
                res = self.format_result(filename, number_files, number_unknown_files, formats, result, allknown)
            dumping_results(res)
            # reset local storage
            self.op.lCOM.clear()
            self.op.ldCOM.clear()
            self.op.stats.clear()
            self.op.stats_puid.clear()
            self.op.lCOM_puid.clear()
            self.op.ldCOM_puid.clear()
            if mode == Mode.pronom:
                self.op.formats_of_current_data_puid.clear()
            else:
                self.op.formats_of_current_data.clear()

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
    def format_result(filename, number_files, number_unknown_files, formats, ranking, allknown):
        result = dict()
        result["filename"] = filename
        result["number_files"] = number_files
        result["number_unknown_files"] = number_unknown_files
        result["formats"] = formats
        for x in ranking:
            result[x[0]] = dict()
            result[x[0]]["co-oc"] = x[1]
        for x in allknown.items():
            result[x[0]]["AllKnownFormatsReadable"] = x[1]
            if x[1] == False:
                result[x[0]]["AllFormatsReadable"] = False
            else:
                if number_unknown_files == 0:
                    result[x[0]]["AllFormatsReadable"] = True
                else:
                    result[x[0]]["AllFormatsReadable"] = False

        return result

def dumping_results(res):
    sep = os.sep
    path = os.path.dirname(os.path.abspath(__file__)) + sep + 'temp_result'
    filename = res["filename"]
    filename1 = filename.split(".").pop(0)
    file = filename1 + "_result.json"
    with open(os.path.join(path, file), 'w+', encoding='utf8', errors='ignore') as json_file:
        json.dump(res, json_file)


def usage():
    string = ""
    string += "python3 main_program.py <Path/to/object/file>\n"


def main(argv):
    if len(argv) != 2:
        usage()
        sys.exit()
    c = Calculator()
    sep = os.sep
    s = argv[1]
    if os.path.isfile(s):
        d = s.split(sep)
        filename = d.pop(-1)
        path = sep.join(d)
        mode = check_mode(path, filename)
        if mode != Mode.pronom and mode != Mode.wikidata:
            print("Either the file does not contain any files or the json cannot be decoded")
            print("or the file format identifier is not \'wikidata\' or \'pronom\'")
            return
        c.setup(mode)
        c.calculate(path, filename, mode)
    elif os.path.isdir(s):
        c.setup_complete()
        c.calculate_whole_folder(s)
    else:
        print("Given path is a special file (socket, FIFO, device file)")


def check_mode(path, filename):
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

        return mode


if __name__ == "__main__":
    main(sys.argv)




