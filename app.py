from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///products.sqlite3"
db = SQLAlchemy(app)

if __name__ == "__main__":
    app.run(debug=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)

class AccountInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class AccountBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, nullable=False)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

    account_balance = AccountBalance.query.first()
    if not account_balance:
        account_balance = AccountBalance(balance=0.0)
        db.session.add(account_balance)
        db.session.commit()

@app.route("/")
def mainpage():
    account_balance = AccountBalance.query.first()
    # account_inventory = AccountInventory.query.all()
    account_inventory = Product.query.all()

    return render_template("mainpage.html", account_inventory=account_inventory, account_balance=account_balance.balance)

@app.route("/purchase-form", methods=("POST", "GET"))
def purchase_form():
    if request.method == "POST":
        product_name = request.form.get("product-name")
        unit_price = float(request.form.get("unit-price"))
        pieces = int(request.form.get("pieces"))
        account_balance = AccountBalance.query.first()

        product = Product.query.filter_by(name=product_name).first()

        if not product:
            product=Product(name=product_name , price=0 , quantity=0 )

        if account_balance.balance >= unit_price*pieces:
            product.quantity += pieces
            product.price= unit_price      
            account_balance.balance -= pieces * unit_price
            transaction = History(product_name=product_name, quantity=pieces, action="Purchase")
            db.session.add(transaction)
            db.session.add(account_balance)
            db.session.add(product)

            db.session.commit()
            print("Purchase successful")

        else:
            print("Product not found or insufficient quantity")

    return render_template("purchase-form.html")

@app.route("/sale-form", methods=("POST", "GET"))
def sale_form():
    if request.method == "POST":
        product_name = request.form.get("product-name-sale")
        unit_price = float(request.form.get("unit-price-sale"))
        quantity = int(request.form.get("pieces-sale"))

        product = Product.query.filter_by(name=product_name).first()

        if product and product.quantity >= quantity:
            product.quantity -= quantity

            account_balance = AccountBalance.query.first()
            account_balance.balance += quantity * unit_price

            transaction = History(product_name=product_name, quantity=quantity, action="Sale")
            db.session.add(transaction)
            db.session.add(account_balance)
            db.session.add(product)

            db.session.commit()
        else:
            print("Product not found or insufficient quantity")

    return render_template("sale-form.html")

@app.route("/balance-change-form", methods=("POST", "GET"))
def balance_change_form():
    if request.method == "POST":
        balance_change_type = request.form.get("type")
        balance_value = float(request.form.get("balance"))

        account_balance = AccountBalance.query.first()

        if balance_change_type == "add":
            account_balance.balance += balance_value
            action = "Added"
        else:
            account_balance.balance -= balance_value
            action = "Subtracted"

        transaction = History(product_name="", quantity=balance_value, action=f"Balance {action}")
        db.session.add(transaction)
        db.session.commit()

    return render_template("balance_change_form.html")

@app.route("/history")
def history_func():
    history_summary = History.query.all()

    return render_template("history.html", history_summary=history_summary)

if __name__ == "__main__":
    app.run(debug=True)