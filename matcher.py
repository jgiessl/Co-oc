
import copy


class Matcher:

    def __init__(self, environmentProcessor):
        self.environmentProcessor = environmentProcessor

    def calculate_object_environment_overlap_weight(self, environmentId, data_object_matrix):
        """
        Calculates the weight of the overlap between the data object and the given environment
        :param environmentId: Id of the environment
        :param data_object_matrix: Matrix which represents format combinations
                                   of the data objects and the specific data object
        :return: Weight of the overlap between the data object and the given environment
        """
        s = set()
        tmp = copy.deepcopy(self.environmentProcessor.readable_formats_of_environment[environmentId])
        while len(tmp) > 0:
            s.add(tmp.pop())
        mat = data_object_matrix.tocoo()
        summ = 0
        for i, j, value in zip(mat.row, mat.col, mat.data):
            if i in s and j in s:
                summ += value
        return summ

    def rank_environments_for_object(self, data_object_matrix):
        """
        Ranks the environments for a data object based upon the format distribution
        of the data objects in general and the specific format distribution of the data object
        :param data_object_matrix: Matrix which represents format combinations
                                   of the data objects and the specific data object
        :return: Sorted list of the likely environments
        """
        tmp = []
        for item in self.environmentProcessor.environmentIdMap.items():
            overlap = self.calculate_object_environment_overlap_weight(item[1], data_object_matrix)
            tmp.append((item[0], overlap))
        return sorted(tmp, key=lambda tup: tup[1], reverse=True)

    def calculate_tf_idf_overlap(self, environmentId, tf_map, idf_map, avdl, dl, k, b):
        """
        Calculates the weight of the overlap between environment and data object based on
        the tf-idf values of the formats
        :param environmentId: Id of the environment
        :param tf_map: Map which stores the tf values of the formats for a given data object
        :param idf_map: idf_map: Map which stores the idf values for each format
        :param avdl: Average document length -> Average number of files in a data object
        :param dl: Document length -> Number of files in data object
        :param k: Control parameter
        :param b: Control parameter
        :return: Weight of the overlap (Score of the environment in respect to a data object)
        """
        tmp = copy.deepcopy(self.environmentProcessor.readable_formats_of_environment[environmentId])
        summ = 0
        s = set()
        while len(tmp) > 0:
            s.add(tmp.pop())
        for formats in s:
            if formats in tf_map:
                summ += Matcher.bm25_formula(tf_map[formats], idf_map[formats], dl, avdl, k, b)
        return summ

    @staticmethod
    def bm25_formula(tf, idf, dl, avdl, k, b):
        """
        Calculates the relevance of a format
        :param tf: Term frequency
        :param idf: Inverse document frequency
        :param dl: Document length -> Number of files in data object
        :param avdl: Average document length -> Average number of files in a data object
        :param k: Control parameter
        :param b: Control parameter
        :return: Score based on the Okapi Bm25 formula
        """
        tf_ = (tf * (k + 1))/(k * (1 - b + b * (dl / avdl)) + tf)
        return tf_ * idf

    def rank_environments_tf_idf(self, tf_map, idf_map, avdl, dl, k, b):
        """
        Ranks all possible Environments according to tf-idf values of the formats
        which are shared by the data object and the environments
        :param tf_map: Map which stores the tf values of the formats for a given data object
        :param idf_map: Map which stores the idf values for each format
        :param avdl: Average document length -> Average number of files in a data object
        :param dl: Document length -> Number of files in data object
        :param k: Control parameter
        :param b: Control parameter
        :return: Sorted list of the likely environments
        """
        tmp = []
        for item in self.environmentProcessor.environmentIdMap.items():
            overlap = self.calculate_tf_idf_overlap(item[1], tf_map, idf_map, avdl, dl, k, b)
            tmp.append((item[0], overlap))
        return sorted(tmp, key=lambda tup: tup[1], reverse=True)







