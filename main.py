import csv
from itertools import islice
from pathlib import Path

from psycopg2.extras import execute_values
import psycopg2
import pandas as pd
import yaml

# To make this secure, this file could be replaced by a local file not included in version control, like .env
# or even Jenkins environment variables for CI/CD, or server environment variables or some other common solution
yaml_file = Path("db-params.yaml")

# Load DB connection parameters from the YAML file
with open(yaml_file, 'r') as fd:
    db_params = yaml.safe_load(fd)

# open a db connection
connection = psycopg2.connect(
    host=db_params["host"],
    database=db_params["db"],
    user=db_params["user"],
    password=db_params["pw"],
)

# get a cursor to send SQL statements to DB
cursor = connection.cursor()

# create table if it doesn't exit
create_table_qry = (
    "create table if not exists stock_data ("
    "pos text, "
    "product text, "
    "date date, "
    "stock integer"
    ");"
)

cursor.execute(create_table_qry)
connection.commit()

# if it exists, truncate to delete previous data, and reset any auto increment values
init_query = 'TRUNCATE TABLE "stock_data" RESTART IDENTITY;'
cursor.execute(init_query)
connection.commit()

csv_file = Path(".").glob("*.[cC][sS][vV]").__next__()
if not csv_file.is_file():
    raise FileNotFoundError(csv_file.resolve())

with open(csv_file, 'r') as fd:
    # create a reader to read CSV file in batches
    reader = csv.reader(fd, delimiter=";")
    next(reader, None)  # skip headers
    # prepare insert SQL statement and other variables to use inside the loop
    batch_idx = 0
    batch_size = 10000
    connection.autocommit = True
    insert_query = 'INSERT INTO stock_data ("pos", "product", "date", "stock") VALUES %s'

    while True:
        batch = list(islice(reader, batch_size))  # grab a batch of data
        if not batch:
            break  # No more data to process, exit loop

        df = pd.DataFrame(batch, columns=["pos", "product", "date", "stock"])
        data_values = [tuple(row) for row in df.values]
        # insert data into db using batch helper function
        execute_values(cursor, insert_query, data_values)

        batch_idx += 1
        print(f"Batch {batch_idx} imported successfully.")

# clean up
cursor.close()
connection.close()
