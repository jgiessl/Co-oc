# Co-occurrence-model for the Recommendation of system environments for data-objects
This program contains two tools. One tool is for the calculation of the recommendations
for system environments. The other tool is for plotting the results of the first tool.
## Recquirements
python 3.8  
matplotlib 3.3.0  
numpy 1.19.1  
scipy 1.5.2  
SPARQLWrapper 1.8.5  
sklearn 0.0 -> scikit-learn 0.23.2  
(should actually work with python 3.x and different versions of the
modules - but there is no guarantee)  
## Usage of the calculation tool
Start the program in console from the program folder by running:   
\>python runner.py  
or rather  
\>python3 runner.py  
  
A Gui should pop up where options can be set for the run and the calculation
can be started.  
After the program is finished there will be a runX folder (X is the number of the current run)
containing a folder called format_co_occurrences, a folder called rankings,
and a text file called run_parameters.txt for a given run and a json file
wikidata_format_entities.json within the save folder of the program.  
run_parameters.txt contains the chosen options of the run.  
wikidata_format_entities.json contains the wikidata-information for all formats in the given data set.  
the rankings folder contains the ranking and miscellaneous information on the individual data-objects of the
data set.  
The format_co_occurrences folder contains files which store the information of the co-occurring formats
for each format.  

### Parameters
#### 1st Option - Path/to/data-objects-folder:  
Select the path to the data-objects that shall be analyzed by entering the
path to the folder in the entry field or simply use the browse button for a file dialog
to choose the data-objects folder. Note that the data-objects need to contain
output of the siegfried(1.7.8) program in jason format.
Furthermore on the first use the displayed default path is not necessarily correct.
Just set the path once on the first use on a new machine. The program will
remember the path afterwards.(Of course the path can be changed with every use)  
A default set of data-objects is in the program folder under the name "sfdata".   

#### 2nd Option - Path/to/environments-folder:  
Select the path to the environments folder against which the data-objects shall be tested
by entering the path to the folder in the entry field or simply use the browse button for a file dialog
to choose the data-objects folder. Note that the environments are described by a json file, which
needs to have the following form:  
{  
"name": "Name of the environment"  
  "programs": ["Wikidata_id_of_program1", "Wikidata_id_of_program2", ...]  
}  
Furthermore on the first use the displayed default path is not necessarily correct.
Just set the path once on the first use on a new machine. The program will
remember the path afterwards.(Of course the path can be changed with every use)  
A default set of environments is in the program folder under the name "environment_collection".  
  

The next four options regard the weight of the co-occurrence-matrices:  
**Co-occurrence-score-matrix =   
(a\*matrix1 + b\*matrix2) "+" (c\*matrix3 + d\*matrix4)**  
(the "+" means that the matrices are not completely added, i.e. the entries of the matrices are
only added if both the entries are not zero) 
#### 3rd Option - Weight of global co-occurrence  

There is the first matrix which represents the the format co-occurrences within data-objects with
respect to all data-objects.   
(a = Weight of global co-occurrences)
the parameter needs to be of double-type. 
#### 4th Option - Weight of global co-occurrences in directories  

There is the second matrix which represents the the format co-occurrences within directories with
respect to all data-objects.   
(b = Weight of global co-occurrences in directories)
the parameter needs to be of double-type.  
#### 5th Option - Weight of local co-occurrence 
  
There is the third matrix which represents the the format co-occurrences within a data-object with
respect to the specific data-object.   
(c = Weight of local co-occurrences)
the parameter needs to be of double-type. 

#### 6th Option - Weight of local co-occurrences in directories  
There is the fourth matrix which represents the the format co-occurrences within directories with
respect to the specific data-object.   
(d = Weight of local co-occurrences in directories)
the parameter needs to be of double-type. 
  
#### 7th Option - Weight of self co-occurrences
This is a correction factor which to accomodate data-objects which contain only
one format - this needs to be a parameter value of double type which should always be
significantly (e.g. two orders magnitude) lower the than the values of the 
previous four options.


The next two options are parameters for the Okapi-BM25 formula which is a version
of a tf-idf-scheme:  
**Format-Score = idf \*(tf \* (k + 1))/(k \* (1 - b + b \* (dl / avdl)) + tf)**  
- where dl is the so-called document length - i.e. the number of files in a data-object  
- where avdl is the average document length - i.e. the average number of files in a data-object  
- where tf is the term frequency - i.e. the number of times a given format occurs in a data-object  
- where idf is the inverse document frequency given by:   
idf(t) = log_2(N_d/ f(t))   
i.e. the logarithm of the number of data-objects divided by the number of documents
containing the format t.  

#### 8th Option - Control parameter k for the okapi-bm25-tf-idf-scheme  
This value represents the k value of the previous mentioned formula and
needs to be of double type.  

#### 9th Option - Control parameter b for the okapi-bm25-tf-idf-scheme  
This value represents the b value of the previous mentioned formula and
needs to be of double type.   

#### 10th Option - Createsave files for the format co-occurrences for each format
If checked json files are created which store the format co-occurrences for each
file format contained in the data set.  

#### 11th Option - Read readable formats for each environment from a save file
If checked the program will read the readable formats for each environment from a save file
(environments_save.json). If the environments stay the same it is encouraged to check this option.
This way the program does not have to contact the WikiData servers every time to ask for the
readable formats of the programs in the environments.  

#### 12th Option - Read readable formats for each environment from a save file
If checked the program will save the readable formats for each environment in the current given path in a save file.
If the environments will stay the same for the next runs check this option on the first run and afterwards use
the previous mentioned option (13th option). And uncheck this option for the following runs.  

#### 13th Option - Print log messages
If checked the program will print log messages to the gui informing the user
of the progress of the program   

## Usage of the plotting tool
The plotting tool can be found in the folder plot_tool.
Start the tool in console from the plot_tool folder folder by running:   
\>python plotter.py  /absolute/path/to/the/run/for/which/plots/shall/be/created

or rather  
\>python3 plotter.py  /absolute/path/to/the/run/for/which/plots/shall/be/created

The plotter has a few options for which plots will be created.
By default(if used as above) the plotter will plot all relevant plots.  
By running:  
\>python plotter.py

or rather  
\>python3 plotter.py
  
  
A more detailed usage message will be displayed.  

#### Results
By default the plotter will create a plot folder in the run folder which contains the different
plots and information files.  
In the format_co_occurrence folder of the plot folder there are plots and info files for each
format (wikidata-ID). The png files show the highest co-occurring formats for the given format.  
The _info.txt files contain the corresponding labels and URIs of the formats (wikidata-IDs).  
  
  
In the rankings folder of the plot folder there are plots and info files for each
ranked data-object. The png files show relative rankings of the different environments.  
The _info.txt files contain the labels and URIs of the formats (wikidata-IDs) of the data-object.  
Furthermore the files contains miscellaneous information on the data-objects.

  






 



 



 

  



