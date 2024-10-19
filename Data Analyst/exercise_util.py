#!/usr/bin/env python3
import io
import os
import pkg_resources
import exercise_util_qc as qc
import pandas as pd
import plotly
import sqlalchemy as alch
import sqlalchemy_utils as alch_utils
from PIL import Image

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
PATH_CSV = os.path.dirname(
    os.path.realpath(__file__)) + "\\source\\"

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
        engine_url = "sqlite:///exercise_database.db"

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

        source_csv = PATH_CSV + table + ".csv"
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

# Write results to sheets in an Excel file and print chart, if applicable.
def write_output(df, sheet_name, fig=None):
    output_dir = os.path.dirname(os.path.realpath(__file__))
    output_path_xlsx = output_dir + '\\exercise_results.xlsx'
    output_path_img = output_dir + f'\\img_{sheet_name.lower()}.png'
    
    if not os.path.exists(output_path_xlsx):
        writer = pd.ExcelWriter(
            path=output_path_xlsx,
            engine='xlsxwriter'
        )
    else:
        writer = pd.ExcelWriter(
            engine='openpyxl',
            mode='a',
            if_sheet_exists='replace',
            path=output_path_xlsx
        )

        
    df.to_excel(excel_writer=writer, 
                sheet_name=sheet_name.lower(), 
                index=False
    )
    writer.close()
    
    if fig != None:
        print("Generating figure...")
        
        # Show and save the figure locally.
        img = plotly.io.to_image(fig=fig,
                                 engine='kaleido',)
        
        Image.open(io.BytesIO(img)).show()

        plotly.io.write_image(fig=fig,
                              file = output_path_img,
                              format='png',
                              engine='kaleido')

        print(f"Figure of {sheet_name} was saved!")