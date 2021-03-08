# Co-oc-tool  
The co-oc-tool provides four 'tools'. The 'main tool' takes the siegfried output of a data-object
in JSON format (the by siegfried used identifier has to be pronom xor wikidata) as input
and recommends(ranks) an environment from a set of environments known to the tool.  
The 'training tool' takes a folder of 'siegfried- JSONs' as specified above to train the
decision model (used in the' main tool').  
The 'environment tool' is for managing the environments the 'main tool' knows.  
To import environments they need to have following form (in JSON format):  
{"name": "<name(key) of the environment>",  
 "programs": [list of wikidataIds("Q...") of the on the environment installed software]  
 }  
The 'managing tool' gives the possibility of adding to and removing environments from
the set of environments known to the 'main tool'.  
The 'cluster tool' takes a folder of 'siegfried- JSONs' and creates plots describing   
the format co-occurrences in a dataset specified by the given folder.    
## Usage  
There are two options of running the tools: Using docker or using the python scripts directly.
###option 1) - using python directly  
#### setup
For this option a python 3.8.x is required (should actually work with python 3.x)  
The necessary packages are written down in the requirements.txt file can be installed using pip:  
pip3 install -r requirements.txt  
#### use cases of the tools
##### main tool
To get an environment recommendation(ranking) for a specific data-object use:  
python3 main_program.py <(absolut)Path/to/object/file.json>

The results are then stored in the temp_result folder
##### training tool
To train the model you can use the training tool as follows:  
To continue the current training use:  
python3 training.py -c <(absolut)Path/to/directory/with/the/trainings/data>

To begin a new training use:  
python3 training.py -n <(absolut)Path/to/directory/with/the/trainings/data>  
##### environment management tool
This tool is for the management of the environments the tool knows about.  
To display the names of the environments the tool knows use:
python3 environment_process.py -d  

To add an environment use:  
python3 environment_process.py -a <(absolut)Path/to/environment/file.json> 

To add a collection of environment use:  
python3 environment_process.py -A <(absolut)Path/to/environment/file/folder>  

To remove a specific environment use:
python3 environment_process.py -r <name of the environment>

To remove all environments use:
python3 environment_process.py -R
##### cluster tool   
To use the cluster tool move to the cluster folder and run  
pip3 install -r requirements.txt  
Then the tool can be used by running  
python3 cluster.py <Path/to/dataset/folder>    
The tool will create the following files in the plots folder:  
a file cluster.png depicting the co-occurrence graph representing the given dataset.  
In Graph edges which have a weight smaller then average edge weight have a blue color.  
Edges which have a weight between the average weight and the average weight + standard deviation  
have a green color.  
Edges which have a weight above the average weight and the average weight + standard deviation  
have a red color.  
Furthermore the tool creates a file info.txt which contains information on the dataset.  
It contains a legend for the file format identifiers and information on the rate of files
for which siegfried could identify the file formats.  
Lastly the tool creates bar plots file format in the in the dataset 
which depict the highest co-occurring formats for a given format.  
By default the ten highest co-occurring formats are plotted if more than ten co-occurring
formats exist. This number can be changed by running the tool with a corresponding option:  
python3 cluster.py <Path/to/dataset/folder> -t \<number>  
  
  
### option 2) use docker

#### setup
If you are using docker for the first time on a specific machine the tool needs to be set up 
if it is already set up this part can be skipped.  
For simplicity run the script setup.sh - it will create the docker images and set up a volume to 
store data.  
(now there should be a volume called co-oc_storage and a non running container co-oc_stor)

#### use cases of the tools
##### main tool
To get an environment recommendation(ranking) for a specific data-object use:  
./main.sh <(absolut)Path/to/object/file.json> <(absolut)Path/to/the/folder/where/the/results/should/go>

##### training tool
To train the model you can use the training tool as follows:  
To continue the current training use:  
./training.sh -c <(absolut)Path/to/directory/with/the/trainings/data>

To begin a new training use:  
./training.sh -n <(absolut)Path/to/directory/with/the/trainings/data>  

##### environment management tool
This tool is for management of the environments the tool knows about.  
To display the names of the environments the tool knows use:
./environment.sh -d  
To add an environment use:  
./environment.sh -a <(absolut)Path/to/environment/file.json> 

To add a collection of environment use:  
./environment.sh -A <(absolut)Path/to/environment/file/folder>  

To remove a specific environment use:
./environment.sh -r <name of the environment>

To remove all environments use:
./environment.sh -R  
  
##### cluster tool  
To use the cluster tool move to the cluster folder and run  
./cluster.sh <(absolut)Path/to/dataset/folder> <(absolut)Path/to/the/folder/where/the/results/should/go>  
The tool will create the following files in the specified folder:  
a file cluster.png depicting the co-occurrence graph representing the given dataset.  
In Graph edges which have a weight smaller then average edge weight have a blue color.  
Edges which have a weight between the average weight and the average weight + standard deviation  
have a green color.  
Edges which have a weight above the average weight and the average weight + standard deviation  
have a red color.  
Furthermore the tool creates a file info.txt which contains information on the dataset.  
It contains a legend for the file format identifiers and information on the rate of files
for which siegfried could identify the file formats.  
Lastly the tool creates bar plots file format in the in the dataset 
which depict the highest co-occurring formats for a given format.  
By default the ten highest co-occurring formats are plotted if more than ten co-occurring
formats exist. This number can be changed by running the tool with a corresponding option:  
./cluster.sh <Path/to/dataset/folder> <(absolut)Path/to/the/folder/where/the/results/should/go> -t \<number>    
