# Co-oc-tool  
The co-oc-tool provides three 'tools'. The 'main tool' takes the siegfried output of a data-object
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

## Usage  
There are two options of running the tools: Using docker or using the python scripts directly.
### option 1) - using python directly  
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
