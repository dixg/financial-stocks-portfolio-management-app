import os
import functools

from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

import numpy as geek

# Configure application
app  = Flask(__name__)
app.debug = True

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached # this file disables caching of responses #
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    stocks=db.execute("SELECT symbol, sum(quantity) AS quantity, cost, sum(total_cost) AS total_cost FROM buy WHERE user_id= :id GROUP BY symbol", id = session["user_id"])
    print("----------- INDEX, stocks_buy db from USER db  =", stocks)
    result = db.execute("SELECT cash FROM users WHERE id = :id", id = session['user_id'])

    total_cash = float(result[0]['cash'])

    grand_total = 0

    for stock in stocks:
            symbol = str(stock['symbol'])
            quantity = stock["quantity"]
            total_cost = stock["total_cost"]
            # price = float(quote['price'])
            grand_total = grand_total+total_cost
            total_cash = float(result[0]['cash'])
            print(" !!!!!!!!!!! total_value_share=",grand_total)





# /    symbol = stocks[0]["symbol"]
    # quantity=stocks[0]["sum(quantity)"]
    # cost=stocks[0]["sum(total_cost)"]
    # print(symbol, quantity, cost)
    # for dict_items in stocks:
    #     print("@@@@@ dict_items[symbol]",dict_items["symbol"])
    #     print("@@@@@ dict_items[sum(quantity]", dict_items["quantity"])
    #     print("@@@@@ dict_items[sum(total_cost]", dict_items["sum(total_cost)"])


    return render_template("index.html", stocks=stocks, cash = total_cash, grand_total = grand_total)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        symbol = request.form["symbol"].upper()
        print("buy  !!!!!!!!!! symbol = ", symbol)

        stock = lookup(symbol)
        print("  ---------------------------------- buy  !!!!!!!!!!  stock", stock)

        bool_value =  symbol in stock.values()
        print("!!!!!!!!!!!!!    bool_value", bool_value)

        if stock == None:
           print("buy  Dict is NULL")

        print("buy  !!!!!!!!!!  stock[price] =", stock["price"])

        if not request.form.get("symbol") or bool_value == False:
            return apology("must provide valid symbol", 403)

        user_id=  session["user_id"]
        username=request.form.get("username")

        print("BUY !!!!!!!  username =", username)
        # User cash
        print(db.execute("SELECT cash FROM users WHERE id= :id",id = session["user_id"]))
        cash = db.execute("SELECT cash FROM users WHERE id= :id",
                        id=session["user_id"])
        print("!!!!!!!!!!!   cash =", cash)

        print("!!!!!!!!!!! cash['cash']", cash[0]['cash'])
        cash_value= cash[0]['cash']
        print("_______@ cash_value", cash_value)

        quantity= request.form.get("shares")
        cost=stock["price"]
        purchase_cost = (float(quantity) * float(cost))
        print("!!!!!    quantity", quantity)
        print("!!!!!    cost", cost)
        print("!!!!!    purchase_cost", purchase_cost)

        dateTimestamp = datetime.now()
        print(dateTimestamp)

        updated_cash=int(cash_value)-int(purchase_cost)

        if updated_cash >= purchase_cost:
            db.execute("UPDATE users SET cash= :updated_cash WHERE id=:id", updated_cash=updated_cash, id=session["user_id"])
            db.execute('INSERT INTO buy(user_id,symbol,quantity,filled,cost,total_cost) VALUES (?,?,?,?,?,?)', (user_id,symbol,quantity,dateTimestamp,cost,purchase_cost))
            print("____   updated_cash", cash_value)
        else:
            return apology("not enough cash avalable for execution!")
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    stocks=db.execute("SELECT symbol, quantity, cost FROM buy WHERE user_id= :id",
    id = session["user_id"])
    print("----------- HISTORY  =   ", stocks)

    # dateTimestamp = datetime.now()
    # print(dateTimestamp)

    for stock in stocks:
            symbol = str(stock['symbol'])
            quantity = stock["quantity"]
            price = stock["cost"]
            status = "BUY"
            filled = datetime.now()

    stocks2=db.execute("SELECT symbol, quantity, sell_price FROM sell  WHERE user_id= :id",
    id = session["user_id"])
    print("----------- HISTORY SELL  =   ", stocks2)

    for stock in stocks2:
            symbol = str(stock['symbol'])
            quantity =  stock["quantity"]
            price = stock["sell_price"]
            status2 = "SELL"
            filled2 = datetime.now()

    return render_template("history.html", stocks=stocks, stocks2=stocks2, status=status, filled=filled, filled2=filled2,  status2=status2 )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    print(">>>",request.form)
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        print(request.form)
        # Ensure username was submitted
        if not request.form.get("username"):
            print(request.form)
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        print("### session[user_id] = ", session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    if request.method == "POST":

        symbol = request.form.get("symbol")

        # lookup retuns dict consisting name, price, symbol
        stock = lookup(symbol)

        if stock == None:
            return apology("incorrect entry", 403)

        else:
            return render_template("quoted.html",stock=stock)

    return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        print("!!!!!!   USERNAME: ",  username)
        print("!!!!!!   password1: ",  password1)
        print("!!!!!!   password2: ",  password2)

        if password1 != password2:
            return redirect(url_for('register'))

        # print("register !!!!!!!!!!!  request.form.get(username) = ", request.form.get("username"))

        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password1"):
            return apology("must provide password", 403)

        elif not request.form.get("password2"):
            return apology("must provide confirmation for password", 403)

        # print("!!!!!! db.execute= ", db.execute('SELECT COUNT (id) FROM users WHERE username = :username', username=request.form.get("username")))
        rows= db.execute('SELECT COUNT (id) FROM users WHERE username = :username', username=request.form.get("username"))
        # print("!!!!!!! rows=",rows[0]['COUNT (id)'])

        number=rows[0]['COUNT (id)']

        if number > 0:
            return apology("username already exists")
        else:
            db.execute('INSERT INTO users (username,hash) VALUES (?, ?)', (username, generate_password_hash(password1)))

            print("!!!!!!   Inserting res=gistered user in the db ")
            # redirect user to Index page, which is our homepage
            return redirect("/")

    return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        symbol = request.form["symbol"].upper()
        print("     sell  !!!!!!!!!! symbol   = ", symbol)

        if not request.form.get("symbol"):
            return apology("Enter symbol", 403)

        stock = lookup(symbol)
        print("     sell  !!!!!!!!!!  stock = lookup(symbol) =  ", stock)

        # Current price of the stock
        current_price=stock["price"]
        print("     sell  !!!!!!!!!!  current_price = =  ", current_price)

        user_id=  session["user_id"]

        stocks=db.execute("SELECT symbol, sum(quantity) AS quantity, cost, sum(total_cost) AS total_cost FROM buy WHERE user_id= :id GROUP BY symbol",
        id = session["user_id"])
        print("     sell    !!!!!!  stocks=", stocks)

        rows=db.execute("SELECT user_id, symbol, sum(quantity) AS quantity, sum(total_cost) AS total_cost FROM buy WHERE user_id= :id AND symbol= :symbol", id = session["user_id"], symbol=symbol)
        print("     sell     !!!!!!!!! ROWS = ", rows)

        if not rows:
             return apology("entred share not found", 403)

        buy_quantity = rows[0]["quantity"]
        print("     sell    !!!!!!!!!   buy_quantity = ", buy_quantity)
        request_quantity = int(request.form.get("shares"))
        print("     sell    !!!!!!!     request_quantity= ", request_quantity)

        available_quantity= buy_quantity-request_quantity
        print("     sell    !!!!!!!     available_quantity = ", available_quantity)

        if request_quantity > available_quantity:
            return apology("    sell   !!!!!!!!!!     Invalid number of shares", 403)

        selling_price=current_price*request_quantity
        print("     !!!!!!!! selling_price =     ", selling_price)

        cash = db.execute("SELECT cash FROM users WHERE id= :id",
                        id=session["user_id"])
        print("!!!!!!!!!!!   cash =", cash)

        print("!!!!!!!!!!! cash['cash']", cash[0]['cash'])
        cash_value= cash[0]['cash']
        print("_______@ cash_value", cash_value)

        # quantity= request.form.get("shares")
        # cost=stock["price"]
        # purchase_cost = (float(quantity) * float(cost))
        # print("!!!!!    quantity", quantity)
        # print("!!!!!    cost", cost)
        # print("!!!!!    purchase_cost", purchase_cost)

        dateTimestamp = datetime.now()
        print(dateTimestamp)

        # updated_cash=int(cash_value)-int(purchase_cost)
        updated_cash = cash_value

        updated_cash = updated_cash+selling_price

        if available_quantity >= request_quantity:
            db.execute("UPDATE users SET cash= :updated_cash WHERE id=:id", updated_cash=updated_cash, id=session["user_id"])
            db.execute('INSERT INTO sell(user_id,symbol,quantity,filled,sell_price) VALUES (?,?,?,?,?)', (user_id,symbol,request_quantity,dateTimestamp,selling_price))




        # db.execute(UPDATE users SET cash= :updated_cash WHERE id=:id", updated_cash=updated_cash, id=session["user_id"])

        # if updated_cash >= purchase_cost:
        #     db.execute("UPDATE users SET cash= :updated_cash WHERE id=:id", updated_cash=updated_cash, id=session["user_id"])
        #     db.execute('INSERT INTO buy(user_id,symbol,quantity,filled,cost,total_cost) VALUES (?,?,?,?,?,?)', (user_id,symbol,quantity,dateTimestamp,cost,purchase_cost))
        #     print("____   updated_cash", cash_value)
        # else:
        #     return apology("not enough cash avalable for execution!")





        # if data is None:
        #     print ('This share was not bought')
        # else:
        #     print ('found')


    return render_template("sell.html")

def errorhandler(e):
    """Handle error"""

    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
