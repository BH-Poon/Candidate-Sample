#!/usr/bin/env python3
import os
import pkg_resources
import exercise_util_qc as qc
import pandas as pd
import sqlalchemy as alch
import sqlalchemy_utils as alch_utils

# Must use this version of kaleido to render the image in reasonable time.
try:
    pkg_resources.require("kaleido==0.1.*")
except:
    os.system("pip install kaleido==0.1.*")

# Parameters for MySQL connection.
USER = "user"
PASSWORD = "pass"
HOST = "host"  # IP address can be used an alternative
PORT = None  # Input port number if applicable
DATABASE = "exercise_database"

# Directory of where the soruce CSV are located.
PATH_DIR_CSV = os.path.dirname(
    os.path.realpath(__file__)) + "\\source\\"

# Directory of where this file is located.
PATH_DIR = os.path.dirname(os.path.realpath(__file__)) + '\\'

EXERCISES = {
    '1': "q2_close_ended.sql",
    '2': "q3_close_ended.sql",
    '3': "q2_open_ended.sql"
}

# Dictionary in the form of table_name: dtype_dict
TABLES = {
    "PRODUCTS_TAKEHOME": {
        "category_1": alch.types.String,
        "category_2": alch.types.String,
        "category_3": alch.types.String,
        "category_4": alch.types.String,
        "manufacturer": alch.types.String,
        "brand": alch.types.String,
        "barcode": alch.types.Integer,
    },
    "TRANSACTION_TAKEHOME": {
        "receipt_id": alch.types.String,
        "purchase_date": alch.types.DateTime,
        "scan_date": alch.types.DateTime,
        "store_name": alch.types.String,
        "user_id": alch.types.String,
        "barcode": alch.types.Integer,
        "final_quantity": alch.types.Numeric,
        "final_sale": alch.types.Numeric,
    },
    "USER_TAKEHOME": {
        "id": alch.types.String,
        "created_date": alch.types.DateTime,
        "birth_date": alch.types.DateTime,
        "state": alch.types.String,
        "language": alch.types.String,
        "gender": alch.types.String,
    }
}

'''
Attempt to connect to MySQL server if available. Otherwise, check for
exercise_database.db and create it from CSV files with SQLite engine
to use for exercise purposes.
'''
def establish_connection():
    
    try:
        engine = alch.create_engine(
            "mysql://{0}:{1}@{2}:{3}/{4}/".format(
                USER, PASSWORD, HOST, PORT, DATABASE),
        )
    except Exception as e:
        print(f"Not connected to MySQL: {e}")
        engine_url = f'sqlite:///{PATH_DIR}/exercise_database.db'

        # Create database using SQLite if there's no database.
        if not alch_utils.database_exists(engine_url):
            create_sample_db(engine_url)
        engine = alch.create_engine(engine_url)

    print("Connected to database... \n")
    return (engine)

# Create the SQL database for exercise purposes.
def create_sample_db(engine_url):

    print("Creating sample database...")
    alch_utils.create_database(engine_url)
    engine = alch.create_engine(engine_url)

    # Load CSV tables.
    for table in TABLES.keys():

        source_csv = PATH_DIR_CSV + table + ".csv"
        col_names = list(TABLES.get(table).keys())

        df = pd.read_csv(
            source_csv, 
            header=0, 
            names=col_names,
            keep_default_na=True 
        )
        df_qc = qc.qc_controller(df, table)
        
        df_qc.to_sql(
            name=table,
            con=engine,
            if_exists="replace",
            index=False,
            dtype=TABLES.get(table),
        )
        print("\tLoaded table: " + table)
    engine.dispose()
    return

def choose_exercise():
    exercise_key = EXERCISES.keys()
    options = ' | '.join(exercise_key)

    # Select from choice with repeated loop for error handling
    while True:
        # Print the options available
        print('Select the exercise to be executed from the following:')
        for key in exercise_key:
            print(f'\t{key} -- {EXERCISES.get(key)}')
        
        # Take in user input and cast as str to compare if it's in list
        input_select_sql = input(f'\nSelect [ {options} ]:  ')
        if input_select_sql in exercise_key:
            return EXERCISES.get(input_select_sql)
        else:
            print('Invalid Input. Please input just the number!\n')

# Disconnect and, if needed, remove sample database for cleanliness.
def disconnect_db(engine):
    
    engine.dispose()
    if os.path.exists("exercise_database.db"):
        try:
            while True:
                input_delet_db = input('Delete sample database?...[Y/N]:  ')
                if input_delet_db.lower() == 'y':
                    os.remove("exercise_database.db")
                    print("Sample database deleted... ")
                    break
                if input_delet_db.lower() == 'n':
                    break
        except Exception as e:
            print(f"Failed to delete sample database... {e}")