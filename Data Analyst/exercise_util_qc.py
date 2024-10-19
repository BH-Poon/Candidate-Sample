#!/usr/bin/env python3
import gc
import re
import warnings
import numpy as np
import exercise_util
import sqlalchemy as alch
import pandas as pd
import pandera as pa
import pandas.api.types as pd_types
from dateutil import parser

# Suppress FutureWarnings... from Pandas...
warnings.filterwarnings(action='ignore', 
                        category=FutureWarning,
)

CHECK_NUMERIC = pa.Check(
    lambda x: pd_types.is_float(x),
    element_wise=True,
)

CHECK_DATETIME = pa.Check(
    lambda x: pd_types.is_datetime64_any_dtype(x),
    element_wise=False,
)

CHECK_INT = pa.Check(
    lambda x: pd_types.is_integer_dtype(x),
    element_wise=False,
)

CHECK_STRING = pa.Check(
    lambda x: pd_types.is_string_dtype(x)
        or x == pd.NA,
    element_wise=False,
)

# Get the datatypes for each column in the table as array.
def clean_string(series, regex_for=None):  
    
    # Convert to Series dtype to string first
    series = series.astype(np.dtype(str))
    
    if regex_for == 'receipt_id':
        regex = r'(?i)[a-z0-9]{8}(-[a-z0-9]{4}){3}-[a-z0-9]{12}'
    
    # Matching for user_id or id (USER_TAKEHOME)
    elif (regex_for == 'user_id') or (regex_for == 'id'):
        regex = r'(?i)[a-z0-9]{24}'
    
    # Specific match and replace for gender values.
    elif series.name == 'gender':
        # For 'non-binary' patterns
        series = series.replace(r'(?i)(non).*(binary)\s', 
                                'non-binary', regex=True).astype(np.dtype(str))
        # For 'not listed' patterns
        series = series.replace(r'(?i)(not).*((list)|(specifi))', 
                                'not listed', regex=True).astype(np.dtype(str))
        # For 'prefer not to say' patterns
        series = series.replace(r'(?i)(prefer).*(not).*', 
                                'not listed', regex=True).astype(np.dtype(str))
   
    # Validation has to be done first because of nulls and strings in pa.Check
    # Wont affect result but will throw long warning prints..
    series = validate_series(series, CHECK_STRING)
    for i, val in series.items():
        
        # Control for null values written as string 'nan'
        if val == 'nan':
            series.loc[i] = np.nan
            continue
        
        # Do left and right cleaning first
        series.loc[i] = re.sub(r'^\s+|\s+$', '', val)
            
        # Do pattern targeting to get those values from string
        if regex_for != None:
            series.loc[i] = re.search(regex,val).string
           
    return series

def clean_datetime(series):

    # Need to iterate due to issue with converting to dtype 
    # from ISO/UTC string inputs
    for i, val in series.items():
  
        # Multi-purpose parser for UTC or ISO8601 datetime strings
        if (val is not np.nan) and (type(val) == str):
            series.loc[i] = pd.Timestamp(parser.parse(val))
        elif (val is None):     # Control for null values
            series.loc[i] = np.nan
        
    # Convert dtype of entire pd.Series
    series = pd.to_datetime(series)
    series = validate_series(series, CHECK_DATETIME) 
    return series

def clean_int(series):
    series = series.replace("-1", np.nan)
    series = series.astype(pd.Int64Dtype())
    series = validate_series(series, CHECK_INT)
    return series

def clean_numeric(series):
    series = series.replace("zero", np.nan)  
    series = series.astype(pd.Float64Dtype())
    series = validate_series(series, CHECK_NUMERIC)
    return series

# Validtes the series based on pre-determined check parameters.
def validate_series(series, check_type):
    schema = pa.SeriesSchema(
        checks=check_type,
        nullable=True,  # Series can contain nulls.
        unique=False,   # Duplicates are okay in series.
        coerce=False   # See if dtype is validated without coercion.
    )   
    try:
        schema.validate(check_obj=series, inplace=True,)
    except Exception as e:
        print(f'VALIDATION FAILED ==> {e}')
        
    return series

def reconcile(df_subset, table=None):
# Reconcile differences in values
    
    # Create array of records and run recursive comparison
    arr_rows = [x for i, x in df_subset.iterrows()]
    arr_reconciled = sub_recur(arr_rows)
    
    # If arr_reconciled has nothing, then move on
    try:
        # Empty out df_subset to keep column information and insert row
        df_subset = df_subset.drop(index=df_subset.index.tolist())
        for rec in arr_reconciled:
            df_subset.loc[0] = rec.copy()
    except:
        pass
    
    return df_subset

def sub_compare(left, right):
        
    # Compare the two series and see if there is a pattern of nulls
    null_compare = left.compare(right).isnull()
    null_vals = null_compare.values.tolist()
    null_tups = [tuple(pair) for pair in null_vals]
    
    # Combinations equates to difference between self and other 
    # with 1=True and 0=False
    good_tups = [(1, 0), (0, 1), (1, 1)]
    
    # No differences between them
    if len(null_tups) == 0:
        arr_choice = [left.combine_first(right)]
    
    # Acceptable combination of null values per column
    elif all(x in good_tups for x in null_tups):
        arr_choice = [left.combine_first(right)]
           
    # Add future controls for when to differentiate two non-nulls...
    else:
        ''' USE FOR TEST TROUBLESHOOTING....
        print(null_compare)
        print(null_tups)
        print('\n', left.to_frame().T, '<---- LEFT\n\n')
        print('\n', right.to_frame().T, '<------- RIGHT\n\n')
        '''
        # Throwing it back for now
        arr_choice = [left] + [right]
    
    return arr_choice

def sub_recur(arr):

    # Directly return
    if len(arr) == 1:
        return arr
    
    # Use compartor function, get result, return
    if len(arr) == 2:
        arr = sub_compare(arr[0],arr[1])
        return arr
    
    # More than 3 records left. Recursion to reconcile failed.
    elif len(arr) > 2:
        
        # Recursive technique
        mid = len(arr) // 2
        arr_left = sub_recur(arr[:mid])
        arr_right = sub_recur(arr[mid:])
        
        # Compile remaining and feed to controller loop
        arr = arr_left + arr_right
        arr_tmp = []
        
        # Finite loop using modified comb sort to eliminate 
        # possibility that reconcile failure was based on position
        for i in range(len(arr)):
            
            # Do sub_compar with different positions
            arr_run = sub_compare(arr[i], arr[(i - 1) // 2])
            
            # Add to arr array if not already in arr 
            [arr_tmp.append(x) for x in arr_run if not any(
                (x == y).all() for y in arr_tmp)]
        
        # Break and return
        arr = arr_tmp
        return arr
 
# Returns column names that are keys for grouping
def get_unique_req(table):
    
    # Accession are id fields for unique identifers and should
    # have the minimum amount of nulls in column
    match table:
       case 'USER_TAKEHOME':     
           unique_req = ['created_date', 'id']
           accession = 'id'
           
       case 'TRANSACTION_TAKEHOME':
           unique_req = ['receipt_id', 'purchase_date',
                         'scan_date', 'store_name', 'user_id']
           accession = 'receipt_id'
           
       case 'PRODUCTS_TAKEHOME':
           unique_req = ['barcode']
           accession = 'barcode'
               
    return accession, unique_req


# Takes subset of N rows and returns 1 row that's reconciled
def qc_by_row(df_tbl, table):
    
    # Garbage collection to free up memory
    gc.collect()
    
    # Remove whitestring spaces
    df_tbl = df_tbl.replace(r'^\s*$', np.nan, regex=True)
    accession, unique_req = get_unique_req(table)
    
    # Just in case there's tables without accessions...
    if accession == None:
        print(f'\tNo accession to use for comparison in {table}!')

    # Keep track of how many rows were removed post-QC
    c_row_start = df_tbl.shape[0]
    
    '''
    Be aware that there are issues with pd.Int64 dtype and using 
    df_tbl.duplicated() as boolean filters. Results are NaN on the 
    accession and will result in removal from main df because of 
    index. Best to copy df_tbl before creating df_dups. Dropping
    nulls from accession column is to prevent reverse action (the
    non-duplicates are removed from main df_tbl).
    '''
    # Copy main df to create df of duplicates. Drop rows with null accessions.
    bool_dups = df_tbl.duplicated(subset=unique_req, keep=False)
    df_dups = df_tbl.copy()     # Avoid unintentional modification of main df.
    df_dups = df_dups[bool_dups.values].dropna(subset=accession)
    
    '''
    # 
    if accession == 'barcode':
        duplicated = df_tbl.duplicated(subset=accession, keep=False)
        df_dups = df_tbl[duplicated.values].dropna(subset=unique_req)
        print(df_dups)
      
    else:
        # Returns all records of the duplicate set
        df_dups = df_tbl[df_tbl.duplicated(subset=unique_req, keep=False)]
    '''   
    
    # No duplications found, return table.
    if df_dups.empty:
        print(f'\tNo duplications found in {table}!')
        return df_tbl
    
    print(f'\tPerforming recursive comparison on {table}...', 
          'WARNING: This might take a while...', sep='\t')
    
    # Iterate through each unique accession value in df_dups
    for acc in df_dups[accession].unique():
        
        # Create subset from df_dups of rows with accession value
        df_subset = df_dups.loc[df_dups[accession] == acc]
                
        # Pass df_subset to reconcile method
        df_reconciled = reconcile(df_subset)
                
        # Drop all rows with the duplicate accession
        df_tbl = df_tbl[df_tbl[accession] != acc]
        
        # Append df_reconciled as rows to df_tbl
        df_tbl = pd.concat([df_tbl,df_reconciled], ignore_index=True, axis=0)
        
        print(f'\t\t... Keeping {df_tbl.shape[0]} out of',
              f' {c_row_start} row(s)', end='\r', sep='')
    
    rows_removed = c_row_start-df_tbl.shape[0]
    print(f'\n\t\t\t... Removed total of {rows_removed} rows from {table}')
    
    return df_tbl


'''
Function for quality control on data. Will also set datatypes and 
confirm that values adhere to the datatype. 
'''
def qc_table(df_tbl, table):  
    # Garbage collection to free up memory
    gc.collect() 
    
    # Columns with preconstructed regex patterns to use
    regex_cols = ['receipt_id', 'user_id', 'id']
    
    print('\tPerforming QC and validation on...')
    for col_name, series in df_tbl.items():
        # Garbage collection to free up memory
        gc.collect()
                
        # Replace whitespace as None for all columns
        series = series.replace(r'^\s*$', np.nan, regex=True)
        print(f'\t\t... {table}.{col_name}')
        
        # QC for specific dtypes
        match exercise_util.TABLES.get(table).get(col_name):
            case alch.types.String:
                regex_for = None
                if col_name in regex_cols:
                    regex_for = col_name
                series_clean = clean_string(series, regex_for)
            case alch.types.Integer:
                series_clean = clean_int(series)
            case alch.types.Numeric:
                series_clean = clean_numeric(series)
            case alch.types.DateTime:
                series_clean = clean_datetime(series)

        # Replace uncleaned series with cleaned series
        df_tbl[col_name] = series_clean.iloc[:]
        
    return df_tbl


def qc_controller(df_tbl, table):
    
    # Make sure dtype is right before curation
    df_tbl = qc_table(df_tbl, table)
    
    # Curate records for issues
    df_tbl = qc_by_row(df_tbl, table)
    
    # Run once more through qc_table before returning
    df_tbl = qc_table(df_tbl, table)
    
    return df_tbl
