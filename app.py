from flask import Flask, render_template, request
import pyodbc

print(pyodbc.drivers())

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
    cursor.execute("SELECT CategoryID, CategoryName FROM ProductCategories")
    categories = cursor.fetchall()

    selected_category = request.form.get('category')
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

    return render_template('index.html', categories=categories, products=products)

if __name__ == '__main__':
    app.run(debug=True)