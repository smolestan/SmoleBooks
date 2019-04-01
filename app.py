import os
import requests 
import json

from flask import Flask, session, render_template, flash, redirect, url_for, request, logging, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from wtforms import Form, StringField, RadioField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#  Index
@app.route("/")
def index():
    return render_template('index.html')

# Register Form Class (using WTforms to be able to validate values inserted)
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        # Get Form Fields
        name = form.name.data
        email = form.email.data
        username = form.username.data
        # Encripting password (creating hash) using sha256
        password = sha256_crypt.encrypt(str(form.password.data))

        # Check if user with this username arleady exists in DB and flashing if true
        result = db.execute("SELECT username FROM users WHERE username = :username", {"username":username}).fetchone()
        if result:
            flash('The user with this username already exists. Please use a different username.', 'danger')
        else:
            # Check if user with this email aleready exists in DB and flashing if true
            result = db.execute("SELECT email FROM users WHERE email = :email", {"email":email}).fetchone()
            if result:
                flash('The user with this email already exists. Please use a different email.', 'danger')
            else:
                # Creating new user in DB and flashing success message
                db.execute("INSERT INTO users(name, email, username, password) VALUES(:name, :email, :username, :password)", {"name": name, "email":email, "username":username, "password":password})
                # Commit to DB
                db.commit()
                flash('You are now registered and can log in', 'success')

                # Redirecting to Login Page
                return redirect(url_for('login'))

    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Get password for given username from DB
        result = db.execute("SELECT password FROM users WHERE username = :username", {"username":username}).fetchone()

        # Check if it exists, than user exists
        if result:
            password = result[0]
        
            # Check if password provided in the form matches with encripted password (aka hash) in DB
            if sha256_crypt.verify(password_candidate, password):
                # Opening session for current user
                session['logged_in'] = True
                session['username'] = username

                # Flashing success message and redirecting to Search Page
                flash('You are now logged in', 'success')
                return redirect(url_for('search'))
            
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

        else: 
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Log out
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Search page
@app.route('/search', methods=["GET", "POST"])
@is_logged_in
def search():
    if request.method == 'POST':
        # Get Form Fields
        isbn = request.form['isbn']
        title = request.form['title']
        author = request.form['author']

        # Checking which fields were completed and adding to variables containing entered data special symbols to perform search in DB even if only part of the value was entered by user 
        if isbn:
            isbn = "%" + isbn + "%"
        if title:
            title = "%" + title + "%"
        if author:
            author = "%" + author + "%"

        # Get from DB books and authors tables info about books with mathing parameters
        results = db.execute("SELECT isbn, title, author, year FROM books JOIN authors ON authors.author_id = books.author_id WHERE isbn LIKE :isbn OR title LIKE :title OR author LIKE :author", {"isbn":isbn, "title":title, "author":author}).fetchall()

        # Rendering page with found books result
        if results:
            return render_template('search.html', results=results)

        # Rendering page with "no such book found" message
        else:
            error = 'Sorry, such book was not found'
            return render_template('search.html', error=error)
    return render_template('search.html')

# Review Form Class
class ReviewForm(Form):
    # Radio field to score the book
    rating = RadioField('Please rate the book', choices=[('1','very bad'),('2','bad'),('3','normal'),('4','good'),('5','very good')])
    # Text area field to leave opinion
    opinion = TextAreaField('and leave your opinion in the field below', [validators.Length(min=10)])

# Book Details page
@app.route('/details/<string:isbn>', methods=['GET', 'POST'])
@is_logged_in
def details(isbn):
    
    # Get info from GoodReads api
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "lC7UcJu8HjEpBEeBS2HdFQ", "isbns":isbn})
    myDict = res.json()
    average_rating = myDict['books'][0]['average_rating']
    ratings_count = myDict['books'][0]['work_ratings_count']

    # Get from DB info about particular book to display on details page
    result = db.execute("SELECT isbn, title, author, year FROM books JOIN authors ON authors.author_id = books.author_id WHERE isbn = :isbn", {"isbn":isbn}).fetchone()

    # Get from DB already existing reviews to display on details page
    reviews = db.execute("SELECT username, rating, opinion FROM reviews JOIN users ON users.id = reviews.user_id WHERE isbn = :isbn", {"isbn":isbn}).fetchall()

    # Check if there is already in the DB a review left by current user
    review = db.execute("SELECT isbn, username FROM reviews JOIN users ON users.id = reviews.user_id WHERE isbn = :isbn AND username = :username", {"isbn":isbn, "username":session['username']}).fetchone()

    form = ReviewForm(request.form)
    if request.method == "POST" and form.validate():
        # Get Form Fields
        rating = form.rating.data
        opinion = form.opinion.data

        # Get current users id from DB
        user = db.execute("SELECT id FROM users WHERE username = :username", {"username":session['username']}).fetchone()
        user_id = user[0]

        # Create review to current book
        db.execute("INSERT INTO reviews(isbn, user_id, rating, opinion) VALUES(:isbn, :user_id, :rating, :opinion)", {"isbn": isbn, "user_id":user_id, "rating":rating, "opinion":opinion})
        # Commit to DB
        db.commit()

        flash('Review Submitted', 'success')
        return redirect(url_for('search'))

    # Render Details page with info, reviews (if exist), review submisssion form (if the is no existing review from current user)
    return render_template('details.html', result=result, form=form, review=review, reviews=reviews, average_rating=average_rating, ratings_count=ratings_count)

# Api
@app.route('/api/<string:isbn>', methods=['GET'])
def api(isbn):
    # Get info from GoodReads api
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "lC7UcJu8HjEpBEeBS2HdFQ", "isbns":isbn})

    # Get info from out DB
    result = db.execute("SELECT title, author, year FROM books JOIN authors ON authors.author_id = books.author_id WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    
    if result:
        # Making a dictionary with data
        data = {
        "title": result[0],
        "author": result[1],
        "year": result[2],
        "isbn": isbn,
        "review_count": res.json()['books'][0]['work_ratings_count'],
        "average_score": res.json()['books'][0]['average_rating']
        }
        # Returning answer in JSON format
        return jsonify(data)

    # Returning error message in JSON format
    return jsonify({"error": "Book with provided ISBN not found"}), 404