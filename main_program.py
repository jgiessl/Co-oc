from process import *
from matcher import *
import json
from analyzer import *
import shutil
import re


def calculate(path_to_objects, path_to_environments, q):

    # getting parameters
    data = get_parameters(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
    g = data["global"]
    gdir = data["global_dir"]
    l = data["local"]
    ldir = data["local_dir"]
    read_from_file = data["read_from_file"]
    save_environments_read = data["save_environments_read"]
    create_format_co_occurrence_save_files = data["create_format_co_occurrence_save_files"]
    offset = data["offset"]
    bm25_k = data["bm25_k"]
    bm25_b = data["bm25_b"]

    # setup_temporary file folder for saving the plots
    setup_temporary_file_folders()
    run_parameters()
    q.put('finished setting up the temporary file folders')

    # create objects and pre_process data
    stat = StatsCollector()
    op = ObjectProcessor(stat)
    ep = EnvironmentProcessor()
    op.pre_process_data_objects(path_to_objects, q)

    global_co_occurrence_matrix = op.calculate_relative_weight_matrix(op.create_csc_matrix_from_dict(op.gCOM))
    global_co_occurrence_matrix_dir = op.calculate_relative_weight_matrix(op.create_csc_matrix_from_dict(op.gdCOM))
    processed_matrix = g * global_co_occurrence_matrix + gdir * global_co_occurrence_matrix_dir

    # formatting matrix for partial addition
    p_m_coo = processed_matrix.tocoo()
    pmf = list(zip(p_m_coo.row, p_m_coo.col, p_m_coo.data))
    processed_matrix_formatted = dict()
    for x in pmf:
        processed_matrix_formatted[(x[0], x[1])] = x[2]
    q.put("finished pre-processing the co-occurrences")

    save_format_definitions(stat.formats)

    if read_from_file:
        ep.read_readable_formats_from_file(op.formatIdMap)
    else:
        ep.pre_process_environments(path_to_environments, op.formatIdMap)
    if save_environments_read:
        ep.write_readable_formats_to_file(op.formatIdMap_reverse)
    m = Matcher(ep)
    op.pre_process_idf(path_to_objects)
    q.put('finished pre-processing the variables for the okapi-bm25-tf-idf score')
    ana = Analyzer(stat)
    if create_format_co_occurrence_save_files:
        ana.global_format_co_occurrences(global_co_occurrence_matrix, global_co_occurrence_matrix_dir,
                                         processed_matrix, q)

    # running through the data objects and ranking the environments for them
    for filename in os.listdir(path_to_objects):

        # processing data object for tf-idf ranking
        pr_tf_idf = op.process_tf(path_to_objects, filename)
        if pr_tf_idf is None:
            continue
        else:
            dl = pr_tf_idf[0]
            tf_map = pr_tf_idf[1]

        # processing data object for co-occurrence ranking
        op.process_data_object(path_to_objects, filename)
        matrix = ldir * op.calculate_relative_weight_matrix(op.create_csc_matrix_from_dict(op.ldCOM))\
                 + l * op.calculate_relative_weight_matrix(op.create_csc_matrix_from_dict(op.lCOM))\

        mat = op.partial_add(matrix, processed_matrix_formatted) + offset * op.create_diagonal_matrix()
        op.lCOM.clear()
        op.ldCOM.clear()
        op.formats_of_current_data.clear()

        # analysing the results
        result = m.rank_environments_for_object(mat)
        res = m.rank_environments_tf_idf(tf_map, op.idf_map, op.avdl, dl, bm25_k, bm25_b)

        if ana.check_for_no_ranking_possible(result, res):
            q.put("None of the ranking schemes can find a possible environment for emulating {0}".format(filename))
            continue
        normalized_ranking = ana.normalize_ranking(result, res)
        ranking_map = ana.concatenate_rankings(normalized_ranking[0], normalized_ranking[1])

        #
        number_files = ana.stats.stats[filename][0]
        number_unknown = ana.stats.stats[filename][1]
        formats = ana.stats.stats[filename][2]
        ana.add_combination_ranking(ranking_map)
        write_rankings_to_file(filename, ranking_map, number_files, number_unknown,
                               formats)

    q.put('finished all rankings')
    # moving results to save folder
    q.put('moving results to save folder')
    move_results_to_save_folder()
    q.put('X')


def get_parameters(path, filename):
    """
    Extracts parameters from jason file
    :param path: Path/To/File
    :param filename: Name of the file
    :return: List of parameters
    """
    with open(os.path.join(path, filename), 'r', encoding='utf8',
              errors='ignore') as f:
        data = json.load(f)
    return data

# def handle_error(func, path, ex_info):
#     """Clear the readonly bit and reattempt the removal"""
#     print(ex_info)
#     if not os.access(path, os.W_OK):
#         os.chmod(path, stat.S_IWUSR)
#     func(path)


def setup_temporary_file_folders():
    """
    Creates the temporary file folders for saving the plots/results
    """
    sep = os.sep
    # set up temporary file folder
    if 'tmp' in os.listdir(os.path.dirname(os.path.abspath(__file__))):
        try:
            pat = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep
            shutil.rmtree(pat, ignore_errors=True)
        except OSError:
            print("Deletion of {0} failed".format(os.path.dirname(os.path.abspath(__file__))
                  + sep + 'tmp' + sep))
    try:
        os.mkdir(os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp')
    except OSError as e:
        print(e)
        print("Creation of the directory {0} failed".format(os.path.dirname(os.path.abspath(__file__))
                                                            + sep + 'tmp'))

    try:
        os.mkdir(os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'rankings')
    except OSError as e:
        print(e)
        print("Creation of the directory {0} failed".format(os.path.dirname(os.path.abspath(__file__))
                                                            + sep + 'tmp' + sep + 'rankings'))

    try:
        os.mkdir(os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'format_co_occurrences')
    except OSError:
        print("Creation of the directory {0} failed".format(os.path.dirname(os.path.abspath(__file__))
              + sep + 'tmp' + sep + 'format_co_occurrences'))


def run_parameters():
    """
    Saves the parameters for the run in a text file
    """
    # getting options
    opt = get_parameters(os.path.dirname(os.path.abspath(__file__)), "parameters.json")

    # formatting string
    tmp = list()
    tmp.append('Weight of the co-occurrences in data-objects: {0}\n'.format(str(opt['global'])))
    tmp.append('Weight of the co-occurrences in directories: {0}\n'.format(str(opt['global_dir'])))
    tmp.append('Weight of the co-occurrences for current data-object: {0}\n'.format(str(opt['local'])))
    tmp.append('Weight of the co-occurrences for the directories of the'
               'current data-object: {0}\n'.format(str(opt['local_dir'])))
    tmp.append('Weight of self co-occurrences (correction parameter): {0}\n'.format(str(opt['offset'])))
    tmp.append('Control parameter k of the okapi-bm25-tf-idf-formula: {0}\n'.format(str(opt['bm25_k'])))
    tmp.append('Control parameter b of the okapi-bm25-tf-idf-formula: {0}\n'.format(str(opt['bm25_b'])))
    if opt['create_format_co_occurrence_save_files']:
        tmp.append('Format-co-occurrence save files were created\n')
    if opt['read_from_file']:
        tmp.append('Readable formats of the Environments were read from save file not WikiData\n')
    if opt['save_environments_read']:
        tmp.append('Readable formats of the Environments were saved to file\n')
    if opt['log']:
        tmp.append('Log -messages were printed in textbox\n')
    s = ''
    for x in tmp:
        s += x

    # writing to file
    sep = os.sep
    path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp'
    with open(os.path.join(path, "run_parameters.txt"), 'w+', encoding='utf8',
              errors='ignore') as f:
        f.write(s)


def save_format_definitions(format_map):
    """
    Saves the format definitions, i.e. Wikidata Id ,Wikidata label and URI.
    :param format_map: Map containing Wikidata ID, label and URI
    """
    sep = os.sep
    path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp'
    file = 'wikidata_format_entities.json'
    with open(os.path.join(path, file), 'w+', encoding='utf8',
              errors='ignore') as json_file:
        json.dump(format_map, json_file)


def move_results_to_save_folder():
    """
    Moves the results to save folder
    """
    sep = os.sep
    save_path = os.path.dirname(os.path.abspath(__file__)) + sep + 'save'
    tmp_path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp'
    shutil.move(tmp_path, save_path)
    if len(os.listdir(os.path.dirname(os.path.abspath(__file__)) + sep + 'save')) == 1:
        os.rename(save_path + sep + 'tmp', save_path + sep + 'run0')
    else:
        run_numbers_str = []
        run_numbers = []
        for folder_name in os.listdir(os.path.dirname(os.path.abspath(__file__)) + sep + 'save'):
            n = re.findall("\d+", folder_name)
            if len(n) == 0:
                continue
            run_numbers_str.append(n[0])
        for x in run_numbers_str:
            run_numbers.append(int(x))
        current_run = str(max(run_numbers) + 1)
        os.rename(save_path + sep + 'tmp', save_path + sep + 'run' + current_run)


def write_rankings_to_file(filename, ranking_map, number_files, number_unknown, formats):
    """
    Writes the rankings to a json file
    :param filename: name of the data-object
    :param ranking_map: map storing the rankings {environment: (co-oc-ranking, tf-idf ranking, combined)}
    :param number_files: number of files contained in the data-object
    :param number_unknown: number of files with unknown format in the data-object
    :param formats:  List of the format ids of the formats contained in the data-object
    """
    sep = os.sep
    name = filename.split('.')[0]
    file = name + '_ranking.json'
    path = os.path.dirname(os.path.abspath(__file__)) + sep + 'tmp' + sep + 'rankings'
    serialize = dict()
    serialize['name'] = name
    serialize['type'] = 'rank'
    serialize['number_files'] = number_files
    serialize['number_unknown'] = number_unknown
    serialize['formats'] = list(formats)
    serialize['environments'] = dict()
    for x in ranking_map:
        tmp = dict()
        tmp['co-oc'] = ranking_map[x][0]
        tmp['tf-idf'] = ranking_map[x][1]
        tmp['combined'] = ranking_map[x][2]
        serialize['environments'][x] = tmp
    with open(os.path.join(path, file), 'w+', encoding='utf8',
              errors='ignore') as json_file:
        json.dump(serialize, json_file)











