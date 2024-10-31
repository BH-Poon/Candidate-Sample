/*  !! Only chart parameters in this block. Must use JSON and prefix 'j_fig' or 'j_trace'. j_fig applies on all traces. !!
 
chart_type=bar
x='total_sales'
y='brand'
j_fig={"data": [{"alignmentgroup": "True","orientation": "h",
        "showlegend": false,"textposition": "auto","type": "bar"
    }],
    "layout": { "xaxis": {"title": {"text": "Total Sales"}},
        "yaxis": {"title": {"text": "Brand"},
        "categoryorder": "total ascending"},
        "title": {"text": "Top 5 Brands by Sales (User Account 6 Months)"},
        "barmode": "relative"}
    }
*/

/*
Query SQL database for the following with one query:
    What are the top 5 brands by sales among users that have had 
    their account for at least six months?
*/


--Create a CTE of qualified transactions from joined tables
WITH qualified_transactions AS (    
    SELECT
        barcode
        , final_quantity
        , final_sale
    FROM 
        TRANSACTION_TAKEHOME t
        LEFT JOIN USER_TAKEHOME u 
            ON t.user_id = u.id
    WHERE 
        JULIANDAY(t.scan_date) - JULIANDAY(u.created_date) >= 183
)       -- There's 183 days in half a year (6 months). Can be simplified with DATEDIFF() function in MySQL.
SELECT 
    p.brand
    , SUM(final_sale) AS total_sales
FROM 
    qualified_transactions qt
    LEFT JOIN PRODUCTS_TAKEHOME p 
        ON qt.barcode = p.barcode
WHERE brand IS NOT NULL         -- Remove NULL in brands
    AND final_quantity > 0      -- Remove final_quantity=0
GROUP BY 
    brand
ORDER BY 
    total_sales DESC
LIMIT 5


