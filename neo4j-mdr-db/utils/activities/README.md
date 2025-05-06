# Check of Activities and find concept ids for activities with no c-code
This folder contains utility program, activity_check_c_code.py, for checking if activity instances have a concept id that is a CDISC code and extracts the NCI hierarchy root (if available). 

Another utility program, activity_suggest_c_code.py, finds concept_id for based on the instance name. It runs through 3 loops to find c-codes. First based on MATCH, then on AND-condition and finally it will generate a suggestion column based on contains-condition returning top 3 hits.

The programs write xls files to the output sub-folder.

## Python virtual environment
To run the python programs a virtual environment is made (.venv). To start it up, open a terminal window and type 

    . ./setup-env.sh. 

The prompt should now have a (.venv) at the beginning.
To close the environment type 'deactivate'

In case the virtual environment is corrupted or in any other way not working then delete the .venv file. To make a new do the following (type in terminal):
>python3 -m venv .venv

> . ./setup-env.sh
   
> pip install -r requirements.txt

## neo4j database
The framework requires connection to a neo4j database containing the Activities (BCs).

The credentials and database url is set in the .development-test-env file, which is not stored in repo (has credentials). Make one from the .development-test-env_template file (copy and rename)

The neo4j database must be running in order to connect to it (if local database, then start the database from the neo4j desktop).





