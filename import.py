import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Get data from CSV file
    f = open("books.csv")
    reader = csv.reader(f)

    line_count = 0
    for isbn, title, author, year in reader:

        # Skiping first line because it is table header
        if line_count == 0:
            line_count += 1
        
        else:
            # Check if author already exists in authors DB table
            result = db.execute("SELECT author_id, author FROM authors WHERE author = :author", {"author":author}).fetchone()
            
            # Store existing authors id and name in variables
            if result:
                author_id = result[0]
                author = result[1]
            
            # Create new author in authors DB table and store values in variables
            else:
                db.execute("INSERT INTO authors (author) VALUES (:author)", {"author": author})
                result = db.execute("SELECT author_id, author FROM authors WHERE author = :author", {"author":author}).fetchone()
                author_id = result[0]
                author = result[1]

            # Adding info about book and author id into books DB table
            db.execute("INSERT INTO books (isbn, title, author_id, year) VALUES (:isbn, :title, :author_id, :year)",
                    {"isbn": isbn, "title": title, "author_id": author_id, "year": year})
            line_count +=1

    # Commit to DB
    db.commit()
    
    # Printing to command line info about amount of items imported
    print(f'Imported {line_count-1} items.')

if __name__ == "__main__":
    main()
