import copy
import time

class Matcher:

    def __init__(self):
        self.readable_formats_of_environment = {}
        self.readable_formats_of_environment_puid = {}

    def calculate_object_environment_overlap_weight(self, environmentId, data_object_matrix):
        """
        Calculates the weight of the overlap between the data object and the given environment
        :param environmentId: Id of the environment
        :param data_object_matrix: Matrix which represents format combinations
                                   of the data objects and the specific data object
        :return: Weight of the overlap between the data object and the given environment
        """
        begin = time.time()
        s = set()
        tmp = copy.deepcopy(self.readable_formats_of_environment[environmentId])
        while len(tmp) > 0:
            s.add(tmp.pop())
        mat = data_object_matrix.tocoo()
        summ = 0
        for i, j, value in zip(mat.row, mat.col, mat.data):
            if i in s and j in s:
                summ += value
        end = time.time()
        print("env-Id: {0} overlap calculation takes {1} seconds".format(environmentId, end - begin))
        return summ

    def calculate_object_environment_overlap_weight_puid(self, environmentId, data_object_matrix):
        """
        Calculates the weight of the overlap between the data object and the given environment
        :param environmentId: Id of the environment
        :param data_object_matrix: Matrix which represents format combinations
                                   of the data objects and the specific data object
        :return: Weight of the overlap between the data object and the given environment
        """
        s = set()
        tmp = copy.deepcopy(self.readable_formats_of_environment_puid[environmentId])
        while len(tmp) > 0:
            s.add(tmp.pop())
        mat = data_object_matrix.tocoo()
        summ = 0
        for i, j, value in zip(mat.row, mat.col, mat.data):
            if i in s and j in s:
                summ += value
        return summ

    def rank_environments_for_object(self, data_object_matrix, environmentIdMap):
        """
        Ranks the environments for a data object based upon the format distribution
        of the data objects in general and the specific format distribution of the data object
        :param data_object_matrix: Matrix which represents format combinations
                                   of the data objects and the specific data object
        :return: Sorted list of the likely environments
        """
        tmp = []
        for item in environmentIdMap.items():
            overlap = self.calculate_object_environment_overlap_weight(item[1], data_object_matrix)
            tmp.append((item[0], overlap))
        return tmp  # sorted(tmp, key=lambda tup: tup[1], reverse=True)

    def rank_environments_for_object_puid(self, data_object_matrix, environmentIdMap):
        """
        Ranks the environments for a data object based upon the format distribution
        of the data objects in general and the specific format distribution of the data object
        :param data_object_matrix: Matrix which represents format combinations
                                   of the data objects and the specific data object
        :return: Sorted list of the likely environments
        """
        tmp = []
        for item in environmentIdMap.items():
            overlap = self.calculate_object_environment_overlap_weight_puid(item[1], data_object_matrix)
            tmp.append((item[0], overlap))
        return tmp  # sorted(tmp, key=lambda tup: tup[1], reverse=True)

    def check_for_all_known_formats(self, offset_matrix, environmentIdMap):
        d = dict()
        mat = offset_matrix.tocoo()
        for item in environmentIdMap.items():
            begin = time.time()
            s = set()
            tmp = copy.deepcopy(self.readable_formats_of_environment[item[1]])
            allknownformats = True
            while len(tmp) > 0:
                s.add(tmp.pop())
            for i, j, value in zip(mat.row, mat.col, mat.data):
                if i not in s:
                    allknownformats = False
                    d[item[0]] = allknownformats
                    allknownformats = True
                    break
            else:
                d[item[0]] = allknownformats
            end = time.time()
            print("check all - env_id: {0} takes {1} seconds".format(item[1], end - begin))
        return d

    def check_for_all_known_formats_puid(self, offset_matrix, environmentIdMap):
        d = dict()
        mat = offset_matrix.tocoo()
        for item in environmentIdMap.items():
            s = set()
            tmp = copy.deepcopy(self.readable_formats_of_environment_puid[item[1]])
            allknownformats = True
            while len(tmp) > 0:
                s.add(tmp.pop())
            for i, j, value in zip(mat.row, mat.col, mat.data):
                if i not in s:
                    allknownformats = False
                    d[item[0]] = allknownformats
                    allknownformats = True
                    break
            else:
                d[item[0]] = allknownformats

        return d






