import sqlite3

def setup_database():

    # Connect to the SQLite database
    conn = sqlite3.connect('news.db')

    # Create a cursor object
    c = conn.cursor()

    # Add 'category' column to 'news' table
    c.execute('''
        ALTER TABLE news
        ADD COLUMN video_filename TEXT
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()