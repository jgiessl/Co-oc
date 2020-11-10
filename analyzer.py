
import os
import json


class StatsCollector:

    def __init__(self):
        # dictionary which holds the number of files, the number of unknown formats and the distinct formats
        # for each data object {name: [number of files, number unknown, list of formats]}
        self.stats = {}

        # Map of Wikidata -format ids to Integer-Ids
        self.formatIdMap = {}

        # Map of Integer-Ids to Wikidata -format ids
        self.formatIdMap_reverse = {}

        # Map of wikidata format definitions
        self.formats = {}


class Analyzer:

    def __init__(self, stats_collector):
        # StatsCollector object
        self.stats = stats_collector

    @staticmethod
    def normalize_ranking(co_occurrence_rank, tf_idf_rank):
        """
        Normalizes the environment rankings (both tf_idf and co-occurrence)
        :param co_occurrence_rank: ranking of environments according to co-occurrence (list of tuples(name, score))
        :param tf_idf_rank: ranking of environments according to tf_idf (list of tuples(name, score))
        :return: normalized ranking for both lists
        """
        sum_co = 0
        sum_tf_idf = 0
        new_co_occurrence_rank = []
        new_tf_idf_rank = []
        for x in co_occurrence_rank:
            sum_co += x[1]
        if sum_co != 0:
            for x in co_occurrence_rank:
                new_co_occurrence_rank.append(list(x))
                new_co_occurrence_rank[-1][1] = x[1]/sum_co
        else:
            new_co_occurrence_rank = co_occurrence_rank
        for x in tf_idf_rank:
            sum_tf_idf += x[1]
        if sum_tf_idf != 0:
            for x in tf_idf_rank:
                new_tf_idf_rank.append(list(x))
                new_tf_idf_rank[-1][1] = x[1] / sum_tf_idf
        else:
            new_tf_idf_rank = tf_idf_rank
        return new_co_occurrence_rank, new_tf_idf_rank

    @staticmethod
    def concatenate_rankings(co_occurrence_rank, tf_idf_rank):
        """
        Concatenate the two rankings into a single map
        :param co_occurrence_rank: co-occurrence ranking
        :param tf_idf_rank: tf-idf ranking
        :return: concatenated map
        """
        mapping = {}
        for x in co_occurrence_rank:
            mapping[x[0]] = [x[1]]
        for x in tf_idf_rank:
            mapping[x[0]].append(x[1])
        return mapping

    @staticmethod
    def add_combination_ranking(mapping):
        """
        Adds the combined tf_idf and co-occurrence ranking to the map
        :param mapping: map with the two ranking scores for each environment
        :return: map with added combined ranking
        """
        for keys in mapping:
            s = sum(mapping[keys]) / 2
            mapping[keys].append(s)
        return mapping

    @staticmethod
    def check_for_no_ranking_possible(co_occurrence_rank, tf_idf_rank):
        """
        Checks if both ranking schemes can or cannot rank
        :param co_occurrence_rank: ranking list of the co-occurrence ranking
        :param tf_idf_rank: ranking list of the tf-idf ranking
        :return: True if no ranking is possible- False otherwise
        """
        sum_co = 0
        sum_tf_idf = 0
        for x in co_occurrence_rank:
            sum_co += x[1]
        for x in tf_idf_rank:
            sum_tf_idf += x[1]

        if sum_co == 0 and sum_tf_idf == 0:
            return True
        else:
            return False

    def global_format_co_occurrences(self, csc_preprocess_matrix_g, csc_preprocess_matrix_d
                                     , csc_preprocess_matrix_c, q):
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
                    format_name = self.stats.formatIdMap_reverse[y]
                    formats.append(format_name)
                    values.append(val)
                    values_d.append(val_d)
                    values_c.append(val_c)
                if y == mat_dim - 1:
                    if len(values) == 0:
                        form = self.stats.formatIdMap_reverse[x]
                        q.put("Format {0} ".format(form)
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
                                n_values_d.append(z/sum_d)
                        for z in values:
                            n_values.append(z/sum_g)
                        for z in values_c:
                            n_values_c.append(z/sum_c)

                        form = self.stats.formatIdMap_reverse[x]
                        serialize = self.create_dictionary_for_json(formats, n_values, n_values_d, n_values_c, form)
                        self.write_co_occurrences_to_file(serialize)

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

    @staticmethod
    def write_co_occurrences_to_file(serialize):
        """
        Writes the co-occurrences of a format to a json file
        """
        name = serialize['name']
        file = name + '_co-occurrences.json'
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'format_co_occurrences'
        serialize['type'] = 'co-oc'
        with open(os.path.join(path, file), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize, json_file)









