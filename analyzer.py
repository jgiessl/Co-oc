import numpy as np
import os
from matplotlib import gridspec
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Visualizer:

    def __init__(self):
        pass

    @staticmethod
    def create_plot_for_data_object(ranking_map, name, number_of_files, number_unknown, formats):
        """
        Creates plots with statistics of a data-object
        :param ranking_map: Stores the ranking (relative) of the environments according
                            to tf-idf and co-occurrence ranking
                            {environment: [co-occurrence, tf-idf, mean sum of both]}
        :param name: Name of the data-object, e.g. xzy.ISO
        :param number_of_files: number of files in the data-object
        :param number_unknown: number of unknown files in the data-object
        :param formats: Set of the formats contained by the data object
        """
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

        # setting up file path to the save the figures
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'ranking_plots' + sep + name + '.png'

        # formatting format text plot
        n_form = list(formats)
        coordinate_x = []
        coordinate_y = []
        annote = []
        row_count = 0
        col_count = 0
        for x in n_form:
            if row_count < 10:
                coordinate_y.append(6 - row_count + 1)
                coordinate_x.append(col_count)
                annote.append(x)
                row_count += 1
            else:
                col_count += 1
                row_count = 0
                coordinate_y.append(6 - row_count + 1)
                coordinate_x.append(col_count)
                row_count += 1

        # setting up the plots
        widthscale_1 = 2 * len(environments)
        widthscale_2 = 2 * 1
        widthscale_3 = col_count + 1
        gs = gridspec.GridSpec(1, 3, width_ratios=[widthscale_1, widthscale_2, widthscale_3])
        fig = plt.figure(figsize=(widthscale_1 + widthscale_2 + widthscale_3 + 3.3, 7))
        width = 0.25
        ax = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        ax3 = plt.subplot(gs[2])
        fig.suptitle('Statistics for data-object {0}'.format(name), fontsize=15)
        fig.add_axes(ax)
        fig.add_axes(ax2)
        fig.add_axes(ax3)

        # plot relevance plot
        x_indexes = np.arange(len(environments))
        bar1 = ax.bar(x_indexes - width, co_occurrence_ranking, width=width, label='co-occurrence')
        bar2 = ax.bar(x_indexes, tf_idf_ranking, width=width, label='tf-idf')
        bar3 = ax.bar(x_indexes + width, added_ranking, width=width, label='combined-mean')
        ax.set_title("Environment Rankings")
        ax.set_xlabel("Environments")
        ax.set_ylabel("Relative Ranking Score")
        ax.set_xticks(x_indexes)
        ax.set_xticklabels(environments)
        ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='xx-small')

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

        # plot number known files
        ax2.bar(1 - width / 2, number_unknown, width=width, label='unknown format')
        ax2.bar(1 + width / 2, number_of_files - number_unknown, width=width, label='known format')
        ax2.set_title('Number of files with \n known and unknown formats')
        ax2.set_ylabel('number of files')
        ax2.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='xx-small')
        ax2.set_xticks([])
        ax.set_xticks([], minor=True)

        # plot known formats
        ax3.set_title('Known formats')
        ax3.scatter(coordinate_x, coordinate_y, marker="")

        for i, txt in enumerate(annote):
            ax3.annotate(txt, (coordinate_x[i], coordinate_y[i]), fontsize='x-small')

        ax3.axes.xaxis.set_visible(False)
        ax3.axes.yaxis.set_visible(False)
        ax3.set_frame_on(False)

        # saving figure
        plt.subplots_adjust(wspace=0.6)
        plt.tight_layout(pad=3.0)
        fig.savefig(path, format='png')
        plt.close(fig)

    @staticmethod
    def create_distinction_plot(tup):
        """
        Creates a plot which shows the the mean differences of the relative scores between
        the highest and the second highest ranked environment for both tf-idf and co-occurrence ranking
        in relation to the number of known formats of the data-objects
        :param tup: contains the number of formats the mean difference in co-occurrence-ranking
                    and the mean difference in tf-idf ranking
                    [number_formats] [mean diff co-oc] [mean diff tf-idf]
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
        ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='xx-small')

        ax1.bar(1 - width / 2, all_dist_co_oc, width=width, label='co-occurrence')
        ax1.bar(1 + width / 2, all_dist_tf_idf, width=width, label='tf-idf')
        ax1.set_ylabel('mean difference between first and second choice')
        ax1.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='xx-small')
        ax1.set_xticks([])

        # saving figure
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'distinction' + '.png'
        plt.tight_layout(pad=3.0)
        plt.savefig(path, format='png')
        plt.close(fig)

    @staticmethod
    def create_plot_for_format_co_occurrences(formats, values, values_d, values_c, name):
        """
        Creates a plot showing the score values of the co-occurring formats for a format
        :param formats: List of formats co-occurring with a format
        :param values: Score values (normalized) of the co-occurrences of the formats in data-objects
        :param values_d: Score values (normalized) of the co-occurrences of the formats in directories.
        :param values_c: Score values (normalized) co-occurrences of the formats in data-objects and directories
                         combined.
        :param name: Format for which the co-occurring formats will be plotted
        """
        # setting up paths and directories
        sep = os.sep
        base_path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'format_co_occurrences'
        n_name = name.replace('/', '#')
        path = base_path + sep + n_name + '.png'

        widthscale = len(values)/16

        # plotting
        width = 0.25
        f, ax = plt.subplots()
        f.set_size_inches(8*widthscale + 0.3, 6)
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


class StatsCollector:

    def __init__(self):
        # dictionary which holds the number of files, the number of unknown formats and the distinct formats
        # for each data object {name: [number of files, number unknown, list of formats]}
        self.stats = {}

        # Map of PUID -format ids to Integer-Ids
        self.formatIdMap = {}

        # Map of Integer-Ids to PUID -format ids
        self.formatIdMap_reverse = {}

        # dictionary which holds the rankings for each object {name: {name_environment: [ranking-co-occ,
        # ranking-tf-idf, combined_mean_ranking]}
        self.rankings = {}


class Analyzer:

    def __init__(self, visualizer, stats_collector):
        # Visualizer Object
        self.visualizer = visualizer
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

    def distinctiveness_first_to_second(self):
        """
        Calculates the the difference in Score (relative) between the highest and the second highest ranked
        environment for both ranking schemes and the number of distinct formats for a data object
        :return: number of different formats, diff in co-occ-ranking , diff in tf-idf ranking
        """
        number_distinct_formats = {}

        ####
        number_formats = []
        distinct_co = []
        distinct_tf = []
        count = 0
        sum_dist_co_oc = 0
        sum_dist_tf_ifd = 0
        for data_object in self.stats.stats:
            if data_object not in self.stats.rankings:
                continue
            number_of_formats = len(self.stats.stats[data_object][2])
            if number_of_formats == 0:
                print('strange things')
                continue
            tmp = self.stats.rankings[data_object].items()
            relative_tf_idf_rank = sorted(tmp, key=lambda tup: tup[1][1], reverse=True)
            relative_co_occ_rank = sorted(tmp, key=lambda tup: tup[1][0], reverse=True)
            co_diff = relative_co_occ_rank[0][1][0] - relative_co_occ_rank[1][1][0]
            tf_diff = relative_tf_idf_rank[0][1][1] - relative_tf_idf_rank[1][1][1]
            count += 1
            sum_dist_co_oc += co_diff
            sum_dist_tf_ifd += tf_diff
            if number_of_formats not in number_distinct_formats:
                number_distinct_formats[number_of_formats] = [[co_diff], [tf_diff]]
            else:
                number_distinct_formats[number_of_formats][0].append(co_diff)
                number_distinct_formats[number_of_formats][1].append(tf_diff)

        sum_dist_co_oc = sum_dist_co_oc / count
        sum_dist_tf_ifd = sum_dist_tf_ifd / count

        for key in number_distinct_formats:
            number_formats.append(key)
            distinct_co.append(sum(number_distinct_formats[key][0]) / len(number_distinct_formats[key][0]))
            distinct_tf.append(sum(number_distinct_formats[key][1]) / len(number_distinct_formats[key][1]))

        return number_formats, distinct_co, distinct_tf, sum_dist_co_oc, sum_dist_tf_ifd

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
                        q.put('plotting co-occurrences for {0}'.format(form))
                        self.visualizer.create_plot_for_format_co_occurrences(formats, n_values, n_values_d, n_values_c,
                                                                              form)









