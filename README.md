# Project 1

Web Programming with Python and JavaScript

I have made a responsive book review website for this project using bootstrap framework. 
You can register with help of form helpers using login and email which are not yet used by another user and then log in using your username and password. I store only encripted passwords (aka hashes) in DB.

Once you are logged in, you are able to search for books by ISBN, title or author even if values are not fully completed, leave reviews for individual books, if you haven't before, and see the reviews made by other people. 

You’ll also see Goodreads ratings from a broader audience. 

If you want you can also query for book details and book reviews programmatically via website’s API on "/api/<isbn>" route.

I have used templates to render such pages as index.html, register.html, login.html, search.html, details.html extending layout.html. Also I have used includes to include navbar, messages and form helpers where they are needed.

Provided for me in this project was a file called books.csv, which is a spreadsheet in CSV format of 5000 different books. Each one has an ISBN number, a title, an author, and a publication year. 

In a Python file called import.py separate from my web application, I have written a program that takes the books and import them into my PostgreSQL database. I am submitting this program with the rest of my project code.

Please watch my code, website and screencast for more details.
DATABASE_URL=postgres://zuxjnhjgmubrss:1c57d974aa6e94119282946350ed973d8ecddaa1ef7101572f32c02e214a65ed@ec2-54-221-243-211.compute-1.amazonaws.com:5432/d7cbljb8griqh8

Thank you! ;)
