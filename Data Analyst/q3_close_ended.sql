/*  !! Only chart parameters in this block. Must use JSON and prefix 'j_fig' or 'j_trace'. j_fig applies on all traces. !!

chart_type=pie
values='percent_total_sale'
labels='generation'
j_fig={"data": [{  
        "hole": 0.3,
        "textinfo": "percent",
        "textfont": {"color": "white", "size": 18},
        "showlegend": true,
        "type": "pie" } 
    ], "layout": { "template": {"layout": {
        "colorway":["#F8766D","#A3A500","#00BF7D","#00B0F6","#E76BF3"]}},
        "title":{"text":"Percentage of Sales in the Health & Wellness Category by Generation"}
    }}
*/

/*
Query SQL database for the following with one query: 
    What is the percentage of sales in the 
    Health & Wellness category by generation ?
*/


WITH qualified_user_transactions AS (
    SELECT 
        t.barcode
        , t.final_sale
        , t.final_quantity
        , u.id
        , u.birth_date
        , CASE
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
    FROM 
        TRANSACTION_TAKEHOME t
        LEFT JOIN USER_TAKEHOME u 
            ON t.user_id = u.id
    WHERE (
        CAST(TIMEDIFF(t.scan_date, u.birth_date) AS int) > 17
    )
        AND (CAST(STRFTIME('%Y', u.birth_date) AS int) > 1907)
)
SELECT 
    p.category_1 AS major_category
    , COUNT(q_ut.id) AS count_users
    , generation
    , SUM(q_ut.final_sale) AS total_sales
    , SUM(q_ut.final_sale) /(
        SELECT 
            SUM(q_ut.final_sale)
        FROM 
            qualified_user_transactions q_ut
            LEFT JOIN PRODUCTS_TAKEHOME p 
                ON q_ut.barcode = p.barcode
        WHERE 
            p.category_1 = 'Health & Wellness'
    ) * 100 AS percent_total_sale
FROM 
    qualified_user_transactions q_ut
    LEFT JOIN PRODUCTS_TAKEHOME p 
        ON q_ut.barcode = p.barcode
WHERE 
    major_category = 'Health & Wellness'
GROUP BY 
    generation
ORDER BY 
    CASE generation
        WHEN 'The Greatest Generation' THEN 0
        WHEN 'The Silent Generation' THEN 1
        WHEN 'Baby Boomers' THEN 2
        WHEN 'Generation X' THEN 3
        WHEN 'Millennials' THEN 4
        WHEN 'Generation Z' THEN 5
        WHEN 'Gen Alpha' THEN 6
    END