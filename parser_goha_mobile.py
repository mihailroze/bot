import sqlite3
import time
import requests
import schedule
from bs4 import BeautifulSoup
import os
import glob

def fetch_page_content(url):
    response = requests.get(url, timeout=5)  # 5 seconds timeout
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Error {response.status_code}: Unable to fetch the page content.")
        return None

def add_missing_spaces(text):
    corrected_text = ""
    for i, char in enumerate(text[:-1]):
        corrected_text += char
        if char == '.' and text[i + 1].isalnum():
            corrected_text += ' '
    corrected_text += text[-1]
    return corrected_text

def extract_latest_news(soup):
    latest_news_section = soup.find("div", {"class": "entry-hub__articles"})

    if not latest_news_section:
        print("Error: Unable to find the latest news section.")
        return None

    latest_news = latest_news_section.find("div", {"class": "articles-snippets__snippet-wrapper"})

    if not latest_news:
        print("Error: Unable to find the latest news item.")
        return None

    news_link = latest_news.find("a", {"class": "article-snippet__image-link"})["href"]
    return news_link

def fetch_news_details(url):
    soup = fetch_page_content(url)
    if not soup:
        return None

    title_section = soup.find("h1", {"class": "entry-article__article-title"})
    if not title_section:
        print("Error: Unable to find the title section.")
        return None
    title = title_section.text.strip() + '.'

    text_section = soup.find("div", {"class": "editor-body entry-article__article-body"})
    if not text_section:
        print("Error: Unable to find the text section.")
        return None
    text = text_section.text.strip()

    text = add_missing_spaces(text)

    # Add the source and hashtag to the end of the text
    text += "\n\nИсточник - goha.ru\n#мобильные_игры"

    media_section = soup.find("div", {"class": "editor-body entry-article__article-body"})

    media_url = None
    media_type = None

    if media_section:
        image_section = media_section.find("img")
        editor_body_youtube = media_section.find("editor-body-youtube")  # Ищем тег 'editor-body-youtube'

        if image_section:
            media_url = image_section["src"]
            media_type = "image"
        elif editor_body_youtube:
            media_url = editor_body_youtube['url']  # Извлекаем URL видео из атрибута 'url'
            media_type = "video"
        else:
            print("Warning: Unable to find the image or video section.")
    else:
        print("Warning: Unable to find the media section.")

    return {
        "title": title,
        "text": text,
        "media_url": media_url,
        "media_type": media_type
    }

def save_to_db(title, text, media_url, media_type, category):
    try:
        conn = sqlite3.connect('news.db')
        c = conn.cursor()

        # Check for duplicates
        c.execute('''
            SELECT * FROM news WHERE title = ?
        ''', (title,))
        if c.fetchone() is not None:
            print("Duplicate news item, skipping")
            return

        # Print out the text for debugging
        print(f"\nText before inserting into DB:\n{text}\n")

        # If no duplicates, insert the new item
        c.execute('''
                INSERT INTO news (title, text, media_url, media_type, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, text, media_url, media_type, category))
        conn.commit()
        print("Data has been successfully inserted into the database.")
    except sqlite3.Error as e:
        print("An error occurred:", e.args[0])
    finally:
        if conn:
            conn.close()
            print("The database connection has been closed.")

def main():
    url = "https://www.goha.ru/mobile-games"
    category = "mobile-games"
    soup = fetch_page_content(url)
    if soup:
        latest_news = extract_latest_news(soup)
        if latest_news:
            print("News Link:", latest_news)

            news_details = fetch_news_details(latest_news)
            if news_details:
                print("\nTitle:", news_details["title"])
                print("\nText:", news_details["text"])
                print("\nMedia URL:", news_details["media_url"])

                save_to_db(news_details["title"], news_details["text"], news_details["media_url"], news_details["media_type"], category)

def job():
    print("Fetching the news...")
    main()

schedule.every(5).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

if __name__ == "__main__":
    main()