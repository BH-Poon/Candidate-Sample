#!/usr/bin/env python3
import exercise_util
import sqlalchemy as alch
import pandas as pd
import plotly.express as px
import tabulate as tab


"""
Query SQL database for the following with one query:
    What are the top 5 brands by sales among users that have had 
    their account for at least six months?
"""
def run_query(engine):
    
    print('Running query for Close-Ended, Question 2...')
    with engine.connect() as conn:
    
        # Common Table Expression (CTE) approach
        sql_query = alch.text(
            """
            WITH qualified_transactions AS (
                SELECT barcode,
                    final_quantity,
                    final_sale
                FROM TRANSACTION_TAKEHOME t
                    LEFT JOIN USER_TAKEHOME u ON t.user_id = u.id
                WHERE JULIANDAY(t.scan_date) - JULIANDAY(u.created_date) >= 183
            )
            SELECT p.brand,
                SUM(final_sale) AS total_sales
            FROM qualified_transactions qt
                LEFT JOIN PRODUCTS_TAKEHOME p ON qt.barcode = p.barcode
            WHERE (brand IS NOT NULL)
                AND (final_quantity > 0)
            GROUP BY brand
            ORDER BY total_sales DESC
            LIMIT 5
            """
        ) 
        
        # Execute query to database and crate
        df_query_result = pd.DataFrame(
            conn.execute(sql_query).fetchall()
        )
     
        # Print results in console.
        print(tab.tabulate(df_query_result, 
                        headers=df_query_result.columns.values, 
                        tablefmt='psql',
                        showindex=False))
        engine.dispose()
        
    '''
    Bar chart created with Plotly and will show in browser window. 
    Please note that this may result in some issues depending on the
    environment/editor that script is ran in. Alternatively, there is
    matplotlib that is also available.
    '''
    fig = px.bar(
        df_query_result,
        x='total_sales',
        y='brand',
        title='Top 5 Brands by Sales (User Account 6 Months)',
        labels={'total_sales': 'Total Sales', 'brand': 'Brand'}
    )

    return df_query_result, fig

if __name__ == "__main__":

    # Connect to database.
    engine = exercise_util.establish_connection()

    # Run the query and write to Excel output.
    df_query_result, fig = run_query(engine)
    exercise_util.write_output(df_query_result, "Q2_Close_Ended", fig)

    # Disconnect from database.
    exercise_util.disconnect_db(engine)
