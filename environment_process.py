
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import json
from json.decoder import JSONDecodeError
import getopt
from training import Mode


class EnvironmentProcessor:

    def __init__(self):
        # Maps environments to Integer-Ids
        self.environmentIdMap = {}
        # Maps Integer-Ids to environment names
        self.environmentIdMap_reverse = {}

        self.idCounter = 0

        # Maps environment Ids to  readable formats (Wikidata-ID)
        self.readable_formats_of_environment = {}

        #
        self.formatIdMap = {}

        self.formatIdMap_reverse = {}

        self.formatIdCounter = 0

        self.formatIdMap_puid = {}

        self.formatIdMap_reverse_puid = {}

        self.formatIdCounter_puid = 0

        self.readable_formats_of_environment_puid = {}

        self.format_map_changed = False

        self.format_map_puid_changed = False

    def add_environment(self, name):
        """
        Adds an environment Id
        :param name: Name of the environment
        """
        if name not in self.environmentIdMap:
            self.environmentIdMap[name] = self.idCounter
            self.environmentIdMap_reverse[self.idCounter] = name
            self.idCounter += 1

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
        :param file_format: PUID of the file
        """
        if file_format not in self.formatIdMap_puid:
            self.formatIdMap_puid[file_format] = self.formatIdCounter_puid
            self.formatIdMap_reverse_puid[self.formatIdCounter_puid] = file_format
            self.formatIdCounter_puid += 1

    def pre_process_environments(self, path, filename, formatIdMap):
        """
        Processes the environments gets the the readable file formats of each environment
        according to WikiData
        :param path: Path/To/Environments-file
        :param formatIdMap: Map which holds an integer Id for each format of the data object corpus
        """
        with open(os.path.join(path, filename), 'r', encoding='utf8', errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                print('Could not decode environment file {0}'.format(filename))
            env = data
            if env["name"] in self.readable_formats_of_environment:
                print("environment name {0} already exists - replacing old environment with name {0}".format(env["name"]))
            else:
                self.add_environment(env["name"])
            readable_formats = set()
            for x in env["programs"]:
                # tmp = self.get_readable_formats_of_program(x, formatIdMap)
                tmp = self.get_readable_formats_of_program_wd(x, formatIdMap)
                readable_formats = readable_formats.union(tmp)
                if self.environmentIdMap[env["name"]] not in self.readable_formats_of_environment:
                    self.readable_formats_of_environment[self.environmentIdMap[env["name"]]] = readable_formats
                else:
                    uni = self.readable_formats_of_environment[self.environmentIdMap[env["name"]]].\
                        union(readable_formats)
                    self.readable_formats_of_environment[self.environmentIdMap[env["name"]]] = uni


    def pre_process_environments_puid(self, path, filename, formatIdMap_puid):
        """
        Processes the environments gets the the readable file formats of each environment
        according to WikiData
        :param path: Path/To/Environments-file
        :param formatIdMap: Map which holds an integer Id for each format of the data object corpus
        """
        with open(os.path.join(path, filename), 'r', encoding='utf8', errors='ignore') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                print('Could not decode environment file {0}'.format(filename))
            env = data
            # print(env["name"])
            if env["name"] in self.readable_formats_of_environment_puid:
                print("environment name {0} already exists - replacing old environment with name {0}".format(env["name"]))
            else:
                self.add_environment(env["name"])
            readable_formats = set()
            for x in env["programs"]:
                tmp = self.get_readable_formats_of_program(x, formatIdMap_puid)
                # tmp = self.get_readable_formats_of_program_wd(x, formatIdMap)
                readable_formats = readable_formats.union(tmp)
                if self.environmentIdMap[env["name"]] not in self.readable_formats_of_environment_puid:
                    self.readable_formats_of_environment_puid[self.environmentIdMap[env["name"]]] = readable_formats
                else:
                    uni = self.readable_formats_of_environment_puid[self.environmentIdMap[env["name"]]].\
                        union(readable_formats)
                    self.readable_formats_of_environment_puid[self.environmentIdMap[env["name"]]] = uni

    def write_readable_formats_to_file(self, formatIdmap_reverse):
        """
        Writes the the readable formats for an environment into a save file
        """
        path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'data' + os.sep + 'environment_data'
        serialize = {}
        for key in self.readable_formats_of_environment:
            formats = []
            tmp = list(self.readable_formats_of_environment[key])
            for x in tmp:
                formats.append(formatIdmap_reverse[x])
            serialize[self.environmentIdMap_reverse[key]] = [formats, key]
        with open(os.path.join(path, "environments_save.json"), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize, json_file)
        print("wrote readable formats to file")


    def write_readable_formats_to_file_puid(self, formatIdmap_reverse_puid):
        """
        Writes the the readable formats for an environment into a save file
        """
        path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'data' + os.sep + 'environment_data'
        serialize = {}
        for key in self.readable_formats_of_environment_puid:
            formats = []
            tmp = list(self.readable_formats_of_environment_puid[key])
            for x in tmp:
                formats.append(formatIdmap_reverse_puid[x])
            serialize[self.environmentIdMap_reverse[key]] = [formats, key]
        with open(os.path.join(path, "environments_save_puid.json"), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(serialize, json_file)
        print("wrote readable formats to file")

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
                print('currently there are no environments known to the program')
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
                print('currently there are no environments known to the program')
                return
            for x in data:
                self.environmentIdMap[x] = data[x][1]
                self.environmentIdMap_reverse[data[x][1]] = x
                format_ids = set()
                for y in data[x][0]:
                    format_ids.add(formatIdmap_puid[y])
                self.readable_formats_of_environment_puid[data[x][1]] = format_ids

    def get_readable_formats_of_program(self, programWDID, formatIdMap_puid):
        """
        Function which gets all the readable for a given programm according to WikiData
        :param programWDID: PUID for a program
        :param formatIdMap: Map which holds an integer Id for each format of the data object corpus
        :return: All the readable formats of a program as specified in WikiData
        """
        # TODO problem: handling of file formats which are not instances of file formats?
        endpoint_url = "https://query.wikidata.org/sparql"
        query = """SELECT ?item
        WHERE
         {
         wd:%s wdt:P1072 ?format .
          ?format wdt:P2748 ?item
         }""" % programWDID

        results = self.get_results(endpoint_url, query)
        formats = set()
        ress = results["results"]["bindings"]
        if len(ress) == 0:
            print("For software with the Id {0} no PUIDs of readable formats can be calculated".format(programWDID))
        for result in ress:
            x = result["item"]["value"]
            formats.add(x)
        res = set()
        for x in list(formats):
            if x not in formatIdMap_puid:
                self.add_format_id_puid(x)
                self.format_map_puid_changed = True
                res.add(formatIdMap_puid[x])
            else:
                res.add(formatIdMap_puid[x])
        return res

    def get_readable_formats_of_program_wd(self, programWDID, formatIdMap):
        """
        Function which gets all the readable for a given programm according to WikiData
        :param programWDID: WikiData ID for a program
        :param formatIdMap: Map which holds an integer Id for each format of the data object corpus
        :return: All the readable formats of a program as specified in WikiData
        """
        # TODO problem: handling of file format which are not instances of file formats?
        endpoint_url = "https://query.wikidata.org/sparql"
        query = """SELECT ?item
        WHERE
         {
         wd:%s wdt:P1072 ?item
         }""" % programWDID

        results = self.get_results(endpoint_url, query)
        formats = set()
        ress = results["results"]["bindings"]
        if len(ress) == 0:
            print("The software with the Id {0} does not have any readable formats specified".format(programWDID))
        for result in ress:
            x = result["item"]["value"]
            temp = x.split('/')
            formats.add(temp[-1])
        res = set()
        for x in list(formats):
            if x not in formatIdMap:
                self.add_format_id(x)
                self.format_map_changed = True
                res.add(formatIdMap[x])
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

    def save_environment_id_map(self):
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'environment_data'
        file = 'environment_id_map.json'
        file1 = 'environment_id_map_reverse.json'
        with open(os.path.join(path, file), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(self.environmentIdMap, json_file)
        with open(os.path.join(path, file1), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(self.environmentIdMap_reverse, json_file)

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
        max_key = 0
        for keys in self.environmentIdMap_reverse:
            # print(keys)
            if keys > max_key:
                max_key = keys
        self.idCounter = max_key + 1

    def load_formatId_maps(self):
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

    def add_environment_to_data(self, path_environment_file):
        sep = os.sep
        l = path_environment_file.split(sep)
        filename = l.pop(-1)
        path = sep.join(l)
        self.pre_process_environments(path, filename, self.formatIdMap)
        self.pre_process_environments_puid(path, filename, self.formatIdMap_puid)
        self.write_readable_formats_to_file(self.formatIdMap_reverse)
        self.write_readable_formats_to_file_puid(self.formatIdMap_reverse_puid)

    def add_environment_collection(self, path_to_collection):
        for filename in os.listdir(path_to_collection):
            self.pre_process_environments(path_to_collection, filename, self.formatIdMap)
            self.pre_process_environments_puid(path_to_collection, filename, self.formatIdMap_puid)
        self.write_readable_formats_to_file(self.formatIdMap_reverse)
        self.write_readable_formats_to_file_puid(self.formatIdMap_reverse_puid)

    def remove_environment(self, key):
        self.read_readable_formats_from_file(self.formatIdMap)
        if key in self.readable_formats_of_environment:
            del self.readable_formats_of_environment[key]
            self.write_readable_formats_to_file(self.formatIdMap_reverse)
            if key in self.environmentIdMap_reverse:
                index = self.environmentIdMap_reverse[key]
                del self.environmentIdMap[index]
                del self.environmentIdMap_reverse[key]
        else:
            print('Environment with the key: {0} does not exist'.format(key))
        self.read_readable_formats_from_file_puid(self.formatIdMap_puid)
        if key in self.readable_formats_of_environment_puid:
            del self.readable_formats_of_environment_puid[key]
            self.write_readable_formats_to_file_puid(self.formatIdMap_reverse_puid)
            if key in self.environmentIdMap_reverse:
                index = self.environmentIdMap_reverse[key]
                del self.environmentIdMap[index]
                del self.environmentIdMap_reverse[key]
        else:
            print('Environment with the key: {0} does not exist'.format(key))

    def pre_process_env_from_format_file(self, path_file):
        with open(path_file, 'r+', encoding='utf8', errors='ignore') as json_file:
            data = json.load(json_file)
        for x in data:
            env_name = data[x]['environmentName']
            self.add_environment(env_name)
            tmp_read_wiki = set()
            tmp_read_puid = set()
            if "defaultSaveParameters" in data[x]:
                for y in data[x]["defaultSaveParameters"]:
                    if y["matchedFormatQID"] != "NULL":
                        if y["matchedFormatQID"] not in tmp_read_wiki:
                            if y["matchedFormatQID"] in self.formatIdMap:
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                            else:
                                self.add_format_id(y["matchedFormatQID"])
                                self.format_map_changed = True
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                    pronom_string = self.strip_pronom(y["matchedFormatPronomID"])
                    if pronom_string != "NULL":
                        if pronom_string not in tmp_read_puid:
                            if pronom_string in self.formatIdMap_puid:
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
                            else:
                                self.add_format_id_puid(pronom_string)
                                self.format_map_puid_changed = True
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
            if "openParameters" in data[x]:
                for y in data[x]["openParameters"]:
                    if y["matchedFormatQID"] != "NULL":
                        if y["matchedFormatQID"] not in tmp_read_wiki:
                            if y["matchedFormatQID"] in self.formatIdMap:
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                            else:
                                self.add_format_id(y["matchedFormatQID"])
                                self.format_map_changed = True
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                    pronom_string = self.strip_pronom(y["matchedFormatPronomID"])
                    if pronom_string != "NULL":
                        if pronom_string not in tmp_read_puid:
                            if pronom_string in self.formatIdMap_puid:
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
                            else:
                                self.add_format_id_puid(pronom_string)
                                self.format_map_puid_changed = True
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
            if "otherSaveParameters" in data[x]:
                for y in data[x]["otherSaveParameters"]:
                    if y["matchedFormatQID"] != "NULL":
                        if y["matchedFormatQID"] not in tmp_read_wiki:
                            if y["matchedFormatQID"] in self.formatIdMap:
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                            else:
                                self.add_format_id(y["matchedFormatQID"])
                                self.format_map_changed = True
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                    pronom_string = self.strip_pronom(y["matchedFormatPronomID"])
                    if pronom_string != "NULL":
                        if pronom_string not in tmp_read_puid:
                            if pronom_string in self.formatIdMap_puid:
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
                            else:
                                self.add_format_id_puid(pronom_string)
                                self.format_map_puid_changed = True
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
            if "exportParameters" in data[x]:
                for y in data[x]["exportParameters"]:
                    if y["matchedFormatQID"] != "NULL":
                        if y["matchedFormatQID"] not in tmp_read_wiki:
                            if y["matchedFormatQID"] in self.formatIdMap:
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                            else:
                                self.add_format_id(y["matchedFormatQID"])
                                self.format_map_changed = True
                                tmp_read_wiki.add(self.formatIdMap[y["matchedFormatQID"]])
                    pronom_string = self.strip_pronom(y["matchedFormatPronomID"])
                    if pronom_string != "NULL":
                        if pronom_string not in tmp_read_puid:
                            if pronom_string in self.formatIdMap_puid:
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
                            else:
                                self.add_format_id_puid(pronom_string)
                                self.format_map_puid_changed = True
                                tmp_read_puid.add(self.formatIdMap_puid[pronom_string])
            self.readable_formats_of_environment[self.environmentIdMap[env_name]] = tmp_read_wiki
            self.readable_formats_of_environment_puid[self.environmentIdMap[env_name]] = tmp_read_puid

    def import_environments_from_format_file(self, path_env_format_file):
        self.pre_process_env_from_format_file(path_env_format_file)
        self.write_readable_formats_to_file(self.formatIdMap_reverse)
        self.write_readable_formats_to_file_puid(self.formatIdMap_reverse_puid)


    @staticmethod
    def strip_pronom(pronom_string):
        temp = pronom_string.replace(" ", "")
        return temp


    @staticmethod
    def remove_all():
        sep = os.sep
        path = os.path.dirname(os.path.abspath(__file__)) + sep + 'data' + sep + 'environment_data'
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))

    def display_environments_names(self):
        self.load_environment_id_map()
        string = ""
        if len(self.environmentIdMap) < 1:
            string += "There are currently no environments available"
        else:
            for key in self.environmentIdMap:
                string += key + "\n"
        print(string)


def main_test(argv):
    ep = EnvironmentProcessor()
    ep.load_formatId_maps()
    ep.load_environment_id_map()
    ep.read_readable_formats_from_file(ep.formatIdMap)
    ep.read_readable_formats_from_file_puid(ep.formatIdMap_puid)
    sep = os.sep
    if len(argv) == 1:
        usage()
    else:
        argument_list = argv[1:]
    # Options
    options = "ha:A:r:Rdi:"

    # Long options
    long_options = ["help", "add=", "AddAll=", "remove=", "RemoveAll", "display", "import="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argument_list, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                usage()
            elif currentArgument in ("-d", "--display"):
                ep.display_environments_names()
            elif currentArgument in ("-a", "--add"):
                ep.add_environment_to_data(currentValue)
                ep.save_environment_id_map()
            elif currentArgument in ("-A", "--AddAll"):
                ep.add_environment_collection(currentValue)
                ep.save_environment_id_map()
            elif currentArgument in ("-r", "--remove"):
                if currentValue in ep.environmentIdMap:
                    ep.remove_environment(ep.environmentIdMap[currentValue])
                    ep.save_environment_id_map()
            elif currentArgument in ("-R", "--RemoveAll"):
                ep.remove_all()
            elif currentArgument in ("-i", "--import"):
                ep.import_environments_from_format_file(currentValue)
                ep.save_environment_id_map()

    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))

    if ep.format_map_changed:
        ep.save_format_id_map_to_files(Mode.wikidata)
    if ep.format_map_puid_changed:
        ep.save_format_id_map_to_files(Mode.pronom)


def usage():
    string = ""
    string += "usage: python3 environment_process.py -h\n"
    string += "                                      -a <Path/to/environment/file>\n"
    string += "                                      -A <Path/to/environment/collection>\n"
    string += "                                      -r <key/name of environment>\n"
    string += "                                      -R\n"
    string += "-h, --help: prints this usage message\n"
    string += "-a, --add <Path/to/environment/file>: adds environment, i.e. <Path/to/environment.json> to the known\n"
    string += "                                      environments\n"
    string += "-A, --AddAll <Path/to/environment/collection>: adds all the environments in the folder\n"
    string += "                                               <Path/to/environment/folder to the known environments\n"
    string += "-r, --remove <key/ name of environment>: removes the environment with the name <name of environment>\n"
    string += "                                         from the known environments\n"
    string += "-R, --RemoveAll: removes all the environments from the known environments. Incl. environment-Ids, i.e.\n"
    string += "                 does a reset\n"
    string += "-d, --display: shows the names/keys of all currently available environments\n"
    print(string)
    sys.exit()


if __name__ == "__main__":
    main_test(sys.argv)
