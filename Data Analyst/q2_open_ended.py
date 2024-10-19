#!/usr/bin/env python3
import exercise_util
import sqlalchemy as alch
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tabulate as tab

"""
Query SQL database for the following with one query:
    Which is the leading brand in the Dips & Salsa category?
    
"""
def run_query(engine):
    
    print('Running query for Open-Ended, Question 2..')
    with engine.connect() as conn:
    
        # define "generation" as what year they're born into
        # qualified transactions... remove questionables
        # from qualified transactions... get total sales 
        # group by sum of sales after grouping by generation
    
        # Generational defintion taken from: 
        # https://libguides.usc.edu/busdem/ag
        sql_query = alch.text(
            """
            SELECT p.brand,
                CASE
                    WHEN p.category_3 = 'Hummus' THEN 'Dips'
                    WHEN p.category_3 = 'Ranch Dip' THEN 'Dips'
                    WHEN p.category_3 = 'Dip Mixes' THEN 'Dips'
                    WHEN p.category_3 = 'Salsa' THEN 'Salsa'
                    WHEN p.category_3 = 'Other Dips' THEN 'Dips'
                    WHEN p.category_3 = 'Guacamole' THEN 'Salsa'
                    WHEN p.category_3 = 'French Onion Dip' THEN 'Dips'
                    WHEN p.category_3 = 'Cheese Dip' THEN 'Dips'
                    WHEN p.category_3 = 'Bean Dip' THEN 'Dips'
                    WHEN p.category_3 = 'Dessert Dips' THEN 'Dips'
                END AS sub_category,
                COUNT(t.barcode) AS total_receipts,
                SUM(t.final_sale) AS total_sales,
                (SUM(t.final_sale)/COUNT(t.receipt_id)) AS avg_sales_per_receipt,
                SUM(t.final_quantity) AS total_qty,
                (SUM(t.final_sale)/SUM(t.final_quantity)) AS avg_sales_per_qty,
                COUNT(t.user_id) AS total_users,
                COUNT((SELECT u.id FROM USER_TAKEHOME u 
                    LEFT JOIN TRANSACTION_TAKEHOME t2 ON u.id = t2.user_id 
                    WHERE t2.barcode = t.barcode)) AS users_in_table,
                COUNT(DISTINCT(t.user_id)) AS distinct_users
            FROM TRANSACTION_TAKEHOME t
                LEFT JOIN PRODUCTS_TAKEHOME p ON t.barcode = p.barcode
            WHERE p.category_2 = 'Dips & Salsa' 
                AND t.final_quantity > 0
                AND brand IS NOT NULL
            GROUP BY p.brand
            ORDER BY total_sales DESC, 
                total_qty DESC
            """ 
        )
        
        # Execute query to database and crate 
        df_query_result = pd.DataFrame(
            conn.execute(sql_query).fetchall()
        )
     
        # Print results in console.
        print(tab.tabulate(df_query_result, 
                            headers=df_query_result.columns.values, 
                            tablefmt='simple_outline',
                            showindex=False))
        engine.dispose()
 
    
    # Create a bar chart based on the results.
    df_dips = df_query_result.loc[
        df_query_result['sub_category']=='Dips']
    df_dips = df_dips.sort_values('total_sales', 
                                  ascending=True)
    
    df_salsa = df_query_result.loc[
        df_query_result['sub_category']=='Salsa']
    df_salsa = df_salsa.sort_values('total_sales', 
                                    ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_dips['brand'],
        y=df_dips['total_sales'],
        name='Avg Sales Per Receipt (Dips)',
        marker_color='lightskyblue',
    ))
    fig.add_trace(go.Bar(
        x=df_salsa['brand'],
        y=df_salsa['total_sales'],
        name='Avg Sales Per Receipt (Salsa)',
        marker_color='lightsalmon',
    )) 
    fig.update_layout(width=1200)

    
    return df_query_result, fig


if __name__ == "__main__":

    # Connect to database.
    engine = exercise_util.establish_connection()   
    
    # Run the query and write to Excel output.
    df_query_result, fig = run_query(engine)
    exercise_util.write_output(df_query_result, "Q2_Open_Ended", fig)

    # Disconnect from database.
    exercise_util.disconnect_db(engine)
