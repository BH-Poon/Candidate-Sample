#!/usr/bin/env python3
import exercise_util
import sqlalchemy as alch
import pandas as pd
import plotly.express as px
import tabulate as tab


"""
Query SQL database for the following with one query:
    What is the percentage of sales in the Health & Wellness 
    category by generation?
"""
def run_query(engine):
    
    print('Running query for Close-Ended, Question 3...')
    with engine.connect() as conn:
    
        # define "generation" as what year they're born into
        # qualified transactions... remove questionables
        # from qualified transactions... get total sales 
        # group by sum of sales after grouping by generation
    
        # Generational defintion taken from: 
        # https://libguides.usc.edu/busdem/ag
        sql_query = alch.text(
            """
            WITH qualified_user_transactions AS (
                SELECT t.barcode,
                    t.final_sale,
                    t.final_quantity,
                    u.id,
                    u.birth_date,
                    CASE
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 1900 AND 1924 THEN 'The Greatest Generation'
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 1925 AND 1945 THEN 'The Silent Generation'
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 1946 AND 1964 THEN 'Baby Boomers'
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 1965 AND 1979 THEN 'Generation X'
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 1980 AND 1994 THEN 'Millennials'
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 1995 AND 2012 THEN 'Generation Z'
                        WHEN CAST(STRFTIME('%Y', u.birth_date) AS int) 
                            BETWEEN 2013 AND 2025 THEN 'Gen Alpha'
                    END AS generation
                FROM TRANSACTION_TAKEHOME t
                    LEFT JOIN USER_TAKEHOME u ON t.user_id = u.id
                WHERE (
                        CAST(TIMEDIFF(t.scan_date, u.birth_date) AS int) > 17
                    )
                    AND (CAST(STRFTIME('%Y', u.birth_date) AS int) > 1907)
            )
            SELECT p.category_1 AS major_category,
                COUNT(q_ut.id) AS count_users,
                generation,
                SUM(q_ut.final_sale) AS total_sales,
                SUM(q_ut.final_sale) /(
                    SELECT SUM(q_ut.final_sale)
                    FROM qualified_user_transactions q_ut
                        LEFT JOIN PRODUCTS_TAKEHOME p ON q_ut.barcode = p.barcode
                    WHERE p.category_1 = 'Health & Wellness'
                ) * 100 AS percent_total_sale
            FROM qualified_user_transactions q_ut
                LEFT JOIN PRODUCTS_TAKEHOME p ON q_ut.barcode = p.barcode
            WHERE major_category = 'Health & Wellness'
            GROUP BY generation
            ORDER BY 
                CASE
                    generation
                    WHEN 'The Greatest Generation' THEN 0
                    WHEN 'The Silent Generation' THEN 1
                    WHEN 'Baby Boomers' THEN 2
                    WHEN 'Generation X' THEN 3
                    WHEN 'Millennials' THEN 4
                    WHEN 'Generation Z' THEN 5
                    WHEN 'Gen Alpha' THEN 6
                END
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
    
    # Create a pie chart based on the results.    
    fig = px.pie(
        df_query_result,
        values='percent_total_sale',
        names='generation',
        title='Percentage of Sales in the Health & Wellness Category by Generation',
        labels='generation'
    )
    
    return df_query_result, fig
if __name__ == "__main__":

    # Connect to database.
    engine = exercise_util.establish_connection()   
    
    # Run the query and write to Excel output.
    df_query_result, fig = run_query(engine)
    exercise_util.write_output(df_query_result, "Q3_Close_Ended", fig)

    # Disconnect from database.
    exercise_util.disconnect_db(engine)
