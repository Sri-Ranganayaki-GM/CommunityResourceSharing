from flask import Flask, render_template, request, redirect, session
from db import db, cursor

import qrcode
import os
import io
import base64
from flask import Response

app = Flask(__name__)
app.secret_key = "community123"


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        sql = """
        INSERT INTO users(name,email,phone,password)
        VALUES(%s,%s,%s,%s)
        """

        values = (name, email, phone, password)

        cursor.execute(sql, values)
        db.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        sql = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        cursor.execute(sql, (email, password))

        user = cursor.fetchone()

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect("/dashboard")

        else:

            return "Invalid Email or Password"

    return render_template("login.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect("/login")

    return render_template(
        "dashboard.html",
        username=session["user_name"]
    )


# ---------------- ADD ITEM ---------------- #

@app.route("/add_item", methods=["GET", "POST"])
def add_item():

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        item_name = request.form["item_name"]
        category = request.form["category"]
        price = request.form["price"]
        deposit = request.form["deposit"]
        description = request.form["description"]

        sql = """
        INSERT INTO items
        (user_id,item_name,category,price,deposit,description,image,availability)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            session["user_id"],
            item_name,
            category,
            price,
            deposit,
            description,
            "default.jpg",
            "Available"
        )

        cursor.execute(sql, values)

        db.commit()

        return redirect("/view_items")

    return render_template("add_item.html")


# ---------------- VIEW ITEMS ---------------- #

# ---------------- VIEW ITEMS ---------------- #
# ---------------- VIEW ITEMS ---------------- #

@app.route("/view_items", methods=["GET"])
def view_items():

    search = request.args.get("search", "")
    category = request.args.get("category", "")

    sql = """
    SELECT *
    FROM items
    WHERE item_name LIKE %s
    """

    values = ["%" + search + "%"]

    if category != "" and category != "All":
        sql += " AND category=%s"
        values.append(category)

    cursor.execute(sql, tuple(values))
    items = cursor.fetchall()

    # Dictionary to store reviews for each item
    item_reviews = {}

    for item in items:

        review_sql = """
        SELECT
            reviews.rating,
            reviews.review

        FROM reviews

        JOIN bookings
        ON reviews.booking_id = bookings.id

        WHERE bookings.item_id=%s
        """

        cursor.execute(review_sql, (item[0],))

        item_reviews[item[0]] = cursor.fetchall()

    return render_template(
        "view_items.html",
        items=items,
        item_reviews=item_reviews,
        search=search,
        category=category
    )
# ---------------- BOOK ITEM ---------------- #

@app.route("/book_item/<int:item_id>", methods=["GET", "POST"])
def book_item(item_id):

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute("SELECT * FROM items WHERE id=%s", (item_id,))
    item = cursor.fetchone()

    if request.method == "POST":

        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        sql = """
        INSERT INTO bookings
        (item_id, borrower_id, start_date, end_date, status)
        VALUES(%s,%s,%s,%s,%s)
        """

        values = (
            item_id,
            session["user_id"],
            start_date,
            end_date,
            "Pending"
        )

        cursor.execute(sql, values)
        db.commit()

        return redirect("/my_bookings")

    return render_template("book_item.html", item=item)


# ---------------- MY BOOKINGS ---------------- #

# ---------------- MY BOOKINGS ---------------- #

@app.route("/my_bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    sql = """
    SELECT
        bookings.id,
        items.item_name,
        bookings.start_date,
        bookings.end_date,
        bookings.status
    FROM bookings
    JOIN items
    ON bookings.item_id = items.id
    WHERE bookings.borrower_id = %s
    """

    cursor.execute(sql, (session["user_id"],))

    bookings = cursor.fetchall()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )

# ---------------- OWNER DASHBOARD ---------------- #

# ---------------- OWNER DASHBOARD ---------------- #

@app.route("/owner_dashboard")
def owner_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    sql = """
    SELECT
        bookings.id,
        items.item_name,
        bookings.borrower_id,
        bookings.start_date,
        bookings.end_date,
        bookings.status

    FROM bookings

    JOIN items
    ON bookings.item_id = items.id

    WHERE items.user_id=%s
    """

    cursor.execute(sql, (session["user_id"],))

    bookings = cursor.fetchall()

    return render_template(
        "owner_dashboard.html",
        bookings=bookings
    )

# ---------------- APPROVE BOOKING ---------------- #

@app.route("/approve_booking/<int:booking_id>")
def approve_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    sql = """
    UPDATE bookings
    SET status='Approved'
    WHERE id=%s
    """

    cursor.execute(sql, (booking_id,))
    db.commit()

    return redirect("/owner_dashboard")


# ---------------- REJECT BOOKING ---------------- #

@app.route("/reject_booking/<int:booking_id>")
def reject_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    sql = """
    UPDATE bookings
    SET status='Rejected'
    WHERE id=%s
    """

    cursor.execute(sql, (booking_id,))
    db.commit()

    return redirect("/owner_dashboard")

# ---------------- ADD REVIEW ---------------- #

@app.route("/add_review/<int:booking_id>", methods=["GET", "POST"])
def add_review(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        rating = request.form["rating"]
        review = request.form["review"]

        sql = """
        INSERT INTO reviews
        (booking_id,rating,review)
        VALUES(%s,%s,%s)
        """

        cursor.execute(
            sql,
            (
                booking_id,
                rating,
                review
            )
        )

        db.commit()

        return redirect("/my_bookings")

    return render_template(
        "add_review.html",
        booking_id=booking_id
    )


# ---------------- GENERATE QR CODE ---------------- #

# ---------------- GENERATE QR CODE ---------------- #

# ---------------- GENERATE QR CODE ---------------- #

@app.route("/generate_qr/<int:booking_id>")
def generate_qr(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT * FROM bookings WHERE id=%s",
        (booking_id,)
    )

    booking = cursor.fetchone()

    if not booking:
        return "Booking Not Found"

    website_url = f"https://community-resource-sharing.onrender.com/verify_booking/{booking_id}"

    # Generate QR code
    img = qrcode.make(website_url)

    # Save QR into memory
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Convert to Base64
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    return render_template(
        "qr_code.html",
        qr_code=qr_code,
        booking_id=booking_id
    )
# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin_login")
def admin_login():

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ---------------- #

@app.route("/admin_dashboard")
def admin_dashboard():

    return render_template("admin_dashboard.html")


# ---------------- PROFILE ---------------- #

# ---------------- PROFILE ---------------- #

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    sql = """
    SELECT *
    FROM users
    WHERE id=%s
    """

    cursor.execute(sql, (session["user_id"],))

    user = cursor.fetchone()

    return render_template(
        "profile.html",
        user=user
    )

# ---------------- EDIT PROFILE ---------------- #

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        sql = """
        UPDATE users
        SET
            name=%s,
            email=%s,
            phone=%s
        WHERE id=%s
        """

        cursor.execute(
            sql,
            (
                name,
                email,
                phone,
                session["user_id"]
            )
        )

        db.commit()

        return redirect("/profile")

    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    return render_template(
        "edit_profile.html",
        user=user
    )

# ---------------- EDIT ITEM ---------------- #

@app.route("/edit_item")
def edit_item():

    return render_template("edit_item.html")


# ---------------- BOOKING HISTORY ---------------- #

@app.route("/booking_history")
def booking_history():

    return render_template("booking_history.html")


if __name__ == "__main__":
    app.run(debug=True)