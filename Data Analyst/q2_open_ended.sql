/*  !! Only chart parameters in this block. Must use JSON and prefix 'j_fig' or 'j_trace'. j_fig applies on all traces. !!

chart_type=bar
x='brand' 
y='total_sales'
j_fig={"data": [{}],
    "layout": { "xaxis": { "title": { "text": "Brands" } },
        "yaxis": {"title": {"text": "Total Sale"}},
        "title": {"text": "Salsa & Dip Brands by Total Sales"},
        "width": 1600}}
trace_1 = {"f_name": "sub_category", "f_value": "Dips",
        "sort_by": "total_sales", "sort_ascending": true} 
j_trace_1 = {"data": [{"marker": {"color": "lightsalmon"},
            "name": "Avg Sales Per Receipt (Salsa)",
            "type": "bar"}], "layout": {}}
trace_2 = {"f_name": "sub_category", "f_value": "Salsa", 
        "sort_by": "total_sales", "sort_ascending": false}
j_trace_2={"data": [{"marker": { "color": "lightskyblue"},
            "name": "Avg Sales Per Receipt (Dips)",
            "type": "bar"}], "layout":{}}
*/

/*
Query SQL database for the following with one query: 
    Which is the leading brand in the Dips & Salsa category?
*/

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
    (SUM(t.final_sale) / COUNT(t.receipt_id)) AS avg_sales_per_receipt,
    SUM(t.final_quantity) AS total_qty,
    (SUM(t.final_sale) / SUM(t.final_quantity)) AS avg_sales_per_qty,
    COUNT(t.user_id) AS total_users,
    COUNT(
        (
            SELECT u.id
            FROM USER_TAKEHOME u
                LEFT JOIN TRANSACTION_TAKEHOME t2 ON u.id = t2.user_id
            WHERE t2.barcode = t.barcode
        )
    ) AS users_in_table,
    COUNT(DISTINCT(t.user_id)) AS distinct_users
FROM TRANSACTION_TAKEHOME t
    LEFT JOIN PRODUCTS_TAKEHOME p ON t.barcode = p.barcode
WHERE p.category_2 = 'Dips & Salsa'
    AND t.final_quantity > 0
    AND brand IS NOT NULL
GROUP BY p.brand
ORDER BY total_sales DESC,
    total_qty DESC