import sqlite3
import sys
import yt_dlp

def download_video(url, id):
    ydl_opts = {
        'outtmpl': f'video/{id}.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    filename = f"{id}.mp4"
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute("UPDATE news SET video_filename = ? WHERE id = ?", (filename, id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    url = sys.argv[1]  # ссылка передается как аргумент командной строки
    id = sys.argv[2]  # id передается как второй аргумент командной строки
    download_video(url, id)