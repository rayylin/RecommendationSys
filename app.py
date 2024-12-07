from flask import Flask, jsonify, render_template, request
import pyodbc

app = Flask(__name__)

cart_data = [
    {"id": 1, "name": "Product 1", "price": 10.99, "quantity": 2},
    {"id": 2, "name": "Product 2", "price": 15.99, "quantity": 1},
]

# Database connection using Windows Authentication
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ray\SQLEXPRESS;'
    'DATABASE=RecSys;'
    'Trusted_Connection=yes;'
)

@app.route('/', methods=['GET', 'POST'])
def index():
    cursor = conn.cursor()

    # Fetch categories
    cursor.execute("""SELECT CategoryID
                            ,CategoryName 
                        FROM ProductCategories""")
    categories = cursor.fetchall()

    selected_category = request.form.get('category')

    cursor.execute("""SELECT [City] + ', ' + [StateCode] + ', ' + [ZipCode] AS zipcode
                        FROM [RecSys].[dbo].[ZipCode]
                       WHERE [Status] = 'A'""")
    codes = cursor.fetchall()

    products = []

    if selected_category:
        cursor.execute(
            """SELECT TOP 9 ProductName
                           ,ImageSource
                           ,OrgPrice
                           ,NewPrice
                           ,CASE WHEN INVENTORY > 0 THEN ''
                            ELSE 'Sold Out' END AS INVENTORY
                 FROM Products 
                WHERE Category = ?""",
            selected_category,
        )
        products = cursor.fetchall()

    return render_template('index.html', categories=categories, products=products, codes=codes)

@app.route('/product/<string:product_id>')
def product_page(product_id):
    # Query the database or fetch product details using the product_id
    product, related_products, codes = get_product_and_related(product_id)
    return render_template('product.html', product=product, related_products=related_products, codes=codes)

def get_product_and_related(product_id):
    

    conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ray\SQLEXPRESS;'
    'DATABASE=RecSys;'
    'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
    
    # Query the database for the product information
    cursor.execute("""
        SELECT ProductName,
               NewPrice,
               OrgPrice,
               Inventory,
               Description,
               ImageSource
          FROM Products
         WHERE ProductName = ?
    """, product_id)
    
    # Fetch the data and convert it to a dictionary
    product_row  = cursor.fetchone()   

    product = {
            'ProductName': product_row.ProductName,
            'NewPrice': product_row.NewPrice,
            'OrgPrice': product_row.OrgPrice,
            'Inventory': product_row.Inventory,
            'Description': product_row.Description,
            'ImageSource': product_row.ImageSource
    } if product_row else None
        
    cursor.execute("""
        SELECT TOP (6)
               CASE WHEN Item = ? THEN Item2
	           ELSE Item  END AS 'ProductName'
	          ,CASE WHEN Item = ? THEN C.ImageSource
	           ELSE B.ImageSource  END AS 'ImageSource'
          FROM [RecSys].[dbo].[GroceryRelationship] A
         INNER JOIN [RecSys].[dbo].[Products] B
            ON A.Item = B.ProductName
         INNER JOIN [RecSys].[dbo].[Products] C
            ON A.Item2 = C.ProductName
         WHERE [ITEM] = ?
            OR [Item2] = ?
         ORDER BY Lift DESC
    """, product_id, product_id, product_id, product_id)
    
    # Fetch the data and convert it to a dictionary
    related_rows  = cursor.fetchall()
    

    related_products = [
        {
            'ProductName': row.ProductName,
            'ImageSource': row.ImageSource
        }  for row in related_rows
    ]


    cursor.execute("""SELECT [City] + ', ' + [StateCode] + ', ' + [ZipCode] AS zipcode
                        FROM [RecSys].[dbo].[ZipCode]
                       WHERE [Status] = 'A'""")
    codes = cursor.fetchall()

    conn.close()
    
    return product, related_products, codes




@app.route('/cart')
def cart():
    userid = "ray"
    conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ray\SQLEXPRESS;'
    'DATABASE=RecSys;'
    'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
    
    # Query the database for the product information
    cursor.execute("""
      SELECT A.[UserID]
            ,A.[ProductID]
            ,A.[quantity]
            ,A.[updatetime]
            ,B.[ProductName]
	        ,B.[NewPrice]
        FROM [RecSys].[dbo].[Cart] A
        INNER JOIN [RecSys].[dbo].[Products] B
            ON A.[ProductID] = B.[productID]
        WHERE A.[UserID] = ?
    """, userid)

    carts  = cursor.fetchall()

    conn.close()

    cd = []
    
    for cart in carts:
        cd.append({"id": cart[1], "name": cart[4], "price": cart[5], "quantity": cart[2]})

    return jsonify(cd)


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product = data['product']
    quantity = data["quantity"]

    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=ray\SQLEXPRESS;'
        'DATABASE=RecSys;'
        'Trusted_Connection=yes;'
        )
    cursor = conn.cursor()
    cmd = "INSERT INTO [RecSys].[dbo].[Cart] VALUES (?, ?, ?, GETDATE())"
    cursor.execute(cmd, ('ray', product, quantity))
    conn.commit() 
    
    conn.close()

    return {"message": f"{product} added to cart successfully"}


if __name__ == '__main__':
    app.run(debug=True)