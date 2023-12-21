## Import large CSV to PostgresSQL database

In this program, I decided to use a CSV reader to manage reading chunks of the CSV file at a time, to avoid loading the whole file to memory (>600MB).
The CSV reader will skip the initial line, since I'm using a single file consistently, with the columns already defined, 
but initially I thought of using _df.columns_ to get the column names or simply parsing the first line of the file.

I load the DB connection parameters (database name, user, password) from a YAML file, so these are highly configurable. 
It could use a hidden yaml file, and encrypted one (if adding support for gnupg),
or even environment variables, which would be the best way to go in Jenkins or other CI/CD software.

With the parameters, I open a connection to the postgresSQL database using psycopg2. I then get a cursor, and create the table anew if it doesn't exist, 
I truncate the table to quickly and efficiently clear any previous data, and then I activate autocommit, so that my chunks of data can commit automatically every time the loop runs.

In a loop that runs until all data has been inserted, the program will take the data, load it to a Pandas dataframe, 
where more processing or cleaning could be done (e.g. parse Date columns, check for NaN values, etc.) and then 
the Dataframe is converted to a tuple, and passed to the psycopg2 helper function execute_values. 
This is not a native PostgresSQL function, but a helper one provided by the wrapper library to more efficiently process batches of data. It claims to be more efficient than executemany.

With a batch size of 10k, it takes 1718 batches to import all the data. But the resource consumption is not very high compared to without batches (e.g.: PC freeze and hangs) 
and the process is easy to interrupt at any time. 

### Requirements
- A running PostgresSQL server (I used PostgresSQL 15 in Ubuntu)
- A database defined for this program
- A role and user with permissions or attributes to create/drop tables in this database
- pip install the requirements
---
### What doesn't work or could improve
- Cleaning the data, checking for NaN, data processing
- Logging
- Using task groups or some coroutine solution to asynchronously process the batches if needed