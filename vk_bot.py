import vk_api
import sqlite3
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import requests

TELEGRAM_BOT_TOKEN = '6199782080:AAG5vzqVFcmC62jroIWJG7JT4Vxhuma7Oy0'
TELEGRAM_CHAT_ID = '796641960'

GROUP_ID = "212791279"  # Replace with your Group ID
TOKEN = "vk1.a.ucHaXF73eCPQ0bkXhBILhbbNXgCJJZqlVPOpR1T6OPzy32sGDhTwIEr_jUvYVvlsSnTrLNKumOhc38K_nlbzkHcEFmv8PbSB7_fkCrE6G_e4O68Kh5ocIa4LV4npdMYGhqF1lyIza_fOkt9a8ULqXOSWqiyVYeGYcw_WQof19JOiLXb2liAaOeJSgpfIdBHzcSSRBxCyOP4ZnS1oGHyCNA"  # Replace with your VK API Token

# log in to VK
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

def get_all_news():
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def send_news_to_telegram():
    # Connect to your SQLite database
    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    # Fetch the latest 10 news items
    c.execute("SELECT * FROM news ORDER BY timestamp DESC LIMIT 10")
    rows = c.fetchall()

    # Loop over the news items
    for row in rows:
        # Extract the title, text, and media URL
        title = row[1]
        text = row[2]
        media_url = row[3]

        # Construct the message text
        message_text = f"{title}\n\n{text}"

        # Send the message to the Telegram bot
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message_text}
        )

        # If a media URL was found
        if media_url:
            # Send the media to the Telegram bot
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "photo": media_url}
            )

    # Close the database connection
    conn.close()
