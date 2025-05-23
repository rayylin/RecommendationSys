from flask import Flask, jsonify, render_template, request
import pyodbc
import openai

from config import key1, openaikey

from Embedding import chatbot_response_rag

okey = openaikey

openai.api_key = okey

app = Flask(__name__)


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

    if request.method == "POST":
        form_type = request.form.get("form_type")



    products = []

    if selected_category:
        cursor.execute(
            """SELECT TOP 9 ProductName
                           ,ImageSource
                           ,OrgPrice
                           ,NewPrice
                           ,ProductID
                           ,CASE WHEN INVENTORY > 0 THEN ''
                            ELSE 'Sold Out' END AS INVENTORY
                 FROM Products 
                WHERE Category = ?""",
            selected_category,
        )
        products = cursor.fetchall()

    selected_zip = request.cookies.get("selected_zip", "")  # Retrieve ZIP from cookie

    return render_template('index.html', categories=categories, products=products, codes=codes)


@app.route("/update_zip", methods=["POST"])
def update_zip():
    data = request.get_json()
    selected_zip = data.get("zip")

    response = jsonify({"updated_zip": selected_zip})
    response.set_cookie("selected_zip", selected_zip, max_age=60*60*24)  # Store for 1 day
    return response


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
       ORDER BY A.[updatetime] DESC
    """, userid)

    carts  = cursor.fetchall()

    conn.close()

    cd = []
    
    for cart in carts:
        cd.append({"id": cart[1], "name": cart[4], "price": cart[5], "quantity": cart[2]})

    return jsonify(cd)


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    userid = "ray"
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

    cmd = "EXEC [RecSys].[dbo].[UpdateCart] ?, ?, ?"
    params = (userid, product, quantity)

    cursor.execute(cmd, params)

    conn.commit()
    conn.close()

    return {"message": f"{product} added to cart successfully"}


@app.route('/delete-from-cart', methods=['POST'])
def delete_from_cart():
    userid = "ray"
    data = request.get_json()
    productid = data['productid']

    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=ray\SQLEXPRESS;'
        'DATABASE=RecSys;'
        'Trusted_Connection=yes;'
        )
    
    cursor = conn.cursor()

    cmd = "EXEC [RecSys].[dbo].[DeleteCart] ?, ?"
    params = (userid, productid)
    
    cursor.execute(cmd, params)

    conn.commit()
    conn.close()

    return {"message": f"{productid} added to cart successfully"}



messages = []
@app.route("/messages", methods=["GET", "POST"])
def handle_messages():
    if request.method == "POST":
        # Add a new message
        data = request.json
        messages.append(data)
        return jsonify({"status": "success"}), 201
    elif request.method == "GET":
        # Return all messages
        return jsonify(messages)
    

# We should perform similarity search and pass text with highest similarity to openai, instead of vector
# to prevent users from sending too many requests to database, we can store vector in redis for caching 
# similarity search: FAISS (Python), RediSearch, Azure AI Search, MongoDB Atlas Search

@app.route("/chat", methods=["POST"])
def chat_with_gpt():
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # Call the OpenAI API
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",  # Specify the model version
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": user_message}
        #     ]
        # )
        # gpt_response = response.choices[0].message.content
        
        storeCookie =  request.cookies.get("selected_zip", "No ZIP selected") # Manhattan, NY, 10001

        store = storeCookie.split(",")[0].strip()


        # call rag from embedding.py
        response = chatbot_response_rag(f"{user_message} in store {store}")


        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)