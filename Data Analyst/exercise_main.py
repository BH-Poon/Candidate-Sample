#!/usr/bin/env python3
import re
import io
import os
import json
import sqlalchemy as alch
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import tabulate as tab
from PIL import Image

import exercise_util



def process_chart_params(raw_params):
    
    dt_params = {}
    for param in raw_params:
        
        # Strip off single quotes everywhere and split by '=' to get
        # parameter [0] and value [1]. Will not affect JSON that use
        # double quotes
        param = re.sub(r'(\')', '', param).strip()
        p_split = re.split('=', param)
        
        # Check if value is JSON string, as indicated by brackets and
        # convert to dict object before adding to value
        if re.search(r'(\{.*\})', p_split[1]):
            p_split[1] = json.loads(p_split[1])
                
        dt_params[p_split[0].strip()] = p_split[1]

    return dt_params

'''
Bar chart created with Plotly and will show in browser window.
Please note that this may result in some issues depending on the
environment/editor that script is ran in. Alternatively, there is
matplotlib that is also available.
'''
# Create and return chart object
def get_chart_obj(chart):
    match chart:
        case 'bar':
            return go.Bar()
        case 'pie':
            return go.Pie()

'''
The JSON for a Figure trace in the SQL file's comment block will 
require performing a test print outside of this script first. The
JSON is written to a file after being extracted fromthe trace 
using: pio.json.to_json_plotly(trace,pretty=True).
Common parameter settings for all traces can be separated into a 
JSON in 'fig' within the SQL file comment block.
'''
def make_fig(df, raw_params):
    
    dt_params = process_chart_params(raw_params)
    fig = go.Figure()

    # Check if there are trace JSONs. Parameter 'trace' and 
    # 'j_trace' comes as a pair. 1) 'trace' contains extra 
    # information about the dataset to filter. 2) 'j_trace'
    # is the trace JSON for that dataset.
    has_trace = False
    trace_keys = []
    for key in dt_params.keys():
        if re.search(r'^(trace)', key, re.IGNORECASE):
            has_trace = True
            trace_keys.append(key)
    
    # If there is j_fig, then set the variable for use later.
    # Schema for j_fig must follow the JSON schema for Plotly 
    # Graph Objects with {data: {...},layout: {...},...} 
    if dt_params['j_fig']:
        j_fig = dt_params['j_fig']
    else:
        j_fig = None
            
    # If there are trace JSONs, will need to add differently
    if has_trace:
        for key in trace_keys:
            dt_trace = dt_params[key]
           
            # Select subfield data from df if necessary
            if dt_trace['f_name']:
                df_trace = df.loc[df[
                    dt_trace['f_name']] == dt_trace['f_value']]
            else: 
                df_trace = df
                
            # Check if there's a sorting order, too
            if dt_trace['sort_by']:
                df_trace = df_trace.sort_values(
                    dt_trace['sort_by'],
                    ascending=dt_trace['sort_ascending'])

            # Get the chart object and add trace
            trace = get_chart_obj(dt_params['chart_type'])
                
            # All traces will use the same field for x-axis and 
            # y-axis. Otherwise, the chart won't make sense.
            trace.update(x=df_trace[dt_params['x']], 
                         y=df_trace[dt_params['y']])
            
            # Update the trace with corresponding j_trace that's 
            # mapped to data in JSON dict. Add trace to figure.
            j_trace = 'j_' + key
            trace.update(dt_params[j_trace]['data'][0])
            fig.add_trace(trace)
  
    # If no trace parameters, create graph object directly
    else:
        trace = get_chart_obj(dt_params['chart_type'])

        if dt_params['chart_type'] == 'bar':
            trace.update(x=df[dt_params['x']], 
                         y=df[dt_params['y']])
                    
        elif dt_params['chart_type'] == 'pie':
            trace.update(values=df[dt_params['values']],
                         labels=df[dt_params['labels']],)
        
        # If there's a j_fig, then apply it before adding to figure 
        if j_fig:
            trace.update(j_fig['data'][0])
        fig.add_trace(trace)
    
    # If there's a j_fig, then apply it to the Figure object for
    # the layout.
    if j_fig['layout']:
        fig.update_layout(j_fig['layout'])
    
    return fig
    

# Write results to sheets in an Excel file and print chart, if applicable.
def write_output(df, sheet_name, fig=None):
    
    # Declare file/directory paths.
    output_dir = os.path.dirname(os.path.realpath(__file__))
    output_path_xlsx = output_dir + '\\exercise_results.xlsx'
    output_path_img = output_dir + f'\\img_{sheet_name.lower()}.png'

    # xlsxwriter can write/create, but only openpyxl can append.
    if not os.path.exists(output_path_xlsx):
        writer = pd.ExcelWriter(path=output_path_xlsx, engine='xlsxwriter')
    else:
        writer = pd.ExcelWriter(
            engine='openpyxl', mode='a', if_sheet_exists='replace', path=output_path_xlsx
        )

    df.to_excel(excel_writer=writer, sheet_name=sheet_name.lower(), index=False)
    writer.close()

    if fig is not None:
        print("Generating figure...")

        # Show and save the figure locally.
        img = pio.to_image(
            fig=fig,
            engine='kaleido',
        )
        
        Image.open(io.BytesIO(img)).show()
        pio.write_image(fig=fig, file=output_path_img, format='png', engine='kaleido')
        print(f"Figure of {sheet_name} was saved!")
        
    return

# Main driver for running SQL query based on selected SQL file
def run_query(engine, sql_file, sql_dir=None):
    
    print(f'Running query from: {sql_file}...')
    sql_path = exercise_util.PATH_DIR + sql_file
    raw_params = []
    
    # Connect to engine and execute query 
    with engine.connect() as conn:
        with open(sql_path, 'r') as sql:
           
            # SQL file must exist in same directory as this script.
            # Optional parameter path_sql for future augmentation.
            sql_query = alch.text(sql.read()) 
        
            # Execute query to database and create dataframe.
            df_query_result = pd.DataFrame(conn.execute(sql_query))
            
            # Point reader back to top of file. Add empty array for
            # compartmentalizing each parameter found in file.
            sql.seek(0,0)
            arr_lines = []
            brackets = 0
            
            for line in sql:
                
                # Remove whitespace, tabs, and newlines from line
                # Strip away any leading or trailing whitespace 
                line = re.sub(r'[\n\t]+', '', line).strip()
                
                # Skip the first line of comment block from SQL file
                # and all whitespace lines
                if re.match(r'/\*', line) or len(line) == 0:
                    continue
                
                # At closing comment, append everything in arr_lines
                # and break from reading
                if re.search(r'(\*/)', line):
                    if arr_lines:
                        raw_params.append(''.join(arr_lines))
                    break
                
                # Count number of open/closed brackets in line
                b_open = len(re.findall(r'\{', line))
                b_close = len(re.findall(r'\}', line))

                # The JSON is all on one line with parameter or there
                # are no JSON brackets in line.
                if (b_open - b_close == 0) and brackets == 0:
                    raw_params.append(line)
                    continue
                    
                # Moved to line with new parameter and openining
                # bracket. Join all in arr_lines and reset track 
                else:
                    arr_lines.append(line)
                
                # Tally the running total 
                brackets = brackets + b_open - b_close
                
                # This should be where all are captured.
                if brackets == 0:
                    raw_params.append(''.join(arr_lines))
                    arr_lines = []
                                           
            # Close connection to resources.
            sql.close()
        engine.dispose()
                 
    # Print results in console.
    print(tab.tabulate(df_query_result, 
                    headers=df_query_result.columns.values, 
                    tablefmt='psql',
                    showindex=False))        
    
    fig = make_fig(df_query_result, raw_params)
    
    return df_query_result, fig

if __name__ == "__main__":

    # Step 1: Connect to database and select which SQL file to run.
    engine = exercise_util.establish_connection()
    sql_file = exercise_util.choose_exercise()
    
    # Step 2: Run the query. Write output to Excel and print chart.
    df_query_result, fig = run_query(engine, sql_file)
    write_output(df_query_result, sql_file, fig)

    # Step 3: Disconnect from database. Delete sample database (if needed).
    exercise_util.disconnect_db(engine)
