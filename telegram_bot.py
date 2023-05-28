import logging
import os
import sqlite3
import asyncio
import requests
from pytube import YouTube
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BotBlocked
from vk_api import VkApi

API_TOKEN = "6199782080:AAG5vzqVFcmC62jroIWJG7JT4Vxhuma7Oy0"  # Замените на ваш Telegram Bot API Token

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

chat_id = '295483305'  # Замените на ваш Chat ID

# Инициализация VkApi
vk_api = VkApi(token='vk1.a.5qaSLBZn5TxKajyzK9Hsdk7T4M07AZRw3Vyl7X8_bJHjQpZQi4KuDtyO_SVkUYliM9wU6Og32MWY-IluDKskxujHKyVG9cHFQPYXGnErQKh_HMt4S0OPH3SIKZZtmv2xI3tnd0bsW39KDgNFb7x905wW0iR5JO7uT_ZfkNinrxm6gwWslbkkfhy-OsL25BTuDUQ5fp4bcYMVmoJBDjV3GQ')  # Замените на ваш VK API Token

# Переменная для отслеживания последней отправленной новости
last_news_sent = None


async def on_startup(dp):
    async def on_startup_notify():
        """
        Уведомление о запуске бота
        """
        await bot.send_message(chat_id, 'Бот был запущен')

    async def check_for_news():
        """
        Проверка новостей в базе данных каждые 5 секунд
        """
        global last_news_sent

        while True:
            await asyncio.sleep(5)  # Ожидание 5 секунд перед следующей проверкой

            # Подключение к базе данных SQLite
            conn = sqlite3.connect('news.db')
            c = conn.cursor()

            # Получение последних новостей
            c.execute("SELECT id, title, text, media_url, timestamp FROM news ORDER BY timestamp DESC LIMIT 10")
            news_items = c.fetchall()

            # Закрытие соединения с базой данных
            conn.close()

            # Если есть новости и они новее, чем последняя отправленная новость
            if news_items and (last_news_sent is None or news_items[0][0] > last_news_sent):
                # Обновление последней отправленной новости
                last_news_sent = news_items[0][0]

                for news_item in news_items:
                    # Извлечение заголовка, текста и ссылки на медиа
                    id, title, text, media_url, timestamp, *_ = news_item

                    # Создание кнопки InlineKeyboardButton
                    markup = types.InlineKeyboardMarkup()
                    button = types.InlineKeyboardButton("Опубликовать в VK", callback_data=str(id))
                    markup.add(button)

                    # Отправка заголовка и текста новости пользователю
                    try:
                        await bot.send_message(chat_id, f"{title}\n\n{text}", reply_markup=markup)
                    except BotBlocked:
                        print(f"Пользователь заблокировал бота: {chat_id}")

                    # Если найдена ссылка на медиа
                    if media_url:
                        # Отправка медиа пользователю
                        try:
                            await bot.send_photo(chat_id, photo=media_url)
                        except Exception as e:
                            print(f"Ошибка при отправке фото: {e}")

    asyncio.create_task(on_startup_notify())
    asyncio.create_task(check_for_news())  # Запуск задачи проверки новостей


@dp.callback_query_handler()
async def process_callback_button(callback_query: types.CallbackQuery):
    id = callback_query.data
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news WHERE id = ?", (id,))
    news_item = c.fetchone()
    if news_item:
        id, title, text, media_url, media_type, timestamp, *_ = news_item

        # Загрузка и публикация видео на стене VK
        if media_type == 'video':
            video_filename = f'{id}.mp4'  # Предполагаем, что имя файла соответствует id новости

            # Проверка наличия видеофайла в директории
            if os.path.isfile(f'video/{video_filename}'):
                video_uploaded = await upload_video(id)

                if video_uploaded:
                    await bot.send_message(callback_query.from_user.id,
                                           "Видео успешно загружено и опубликовано на стене VK")
                else:
                    await bot.send_message(callback_query.from_user.id, "Ошибка при загрузке видео на стену VK")
            else:
                await bot.send_message(callback_query.from_user.id, "Видеофайл не найден в директории 'video'")

    else:
        await bot.send_message(callback_query.from_user.id, "Не найдено новостей для выбранного идентификатора")
    conn.close()


@dp.message_handler(commands=['checknews'])
async def cmd_check_news(message: types.Message):
    """
    Немедленная проверка новостей в базе данных
    """
    global last_news_sent

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    # Получение последних новостей
    c.execute("SELECT id, title, text, media_url, timestamp FROM news ORDER BY timestamp DESC LIMIT 10")
    news_items = c.fetchall()

    # Закрытие соединения с базой данных
    conn.close()

    # Если есть новости и они новее, чем последняя отправленная новость
    if news_items and (last_news_sent is None or news_items[0][0] > last_news_sent):
        # Обновление последней отправленной новости
        last_news_sent = news_items[0][0]

        for news_item in news_items:
            # Извлечение заголовка, текста и ссылки на медиа
            id, title, text, media_url, timestamp, *_ = news_item

            # Создание кнопки InlineKeyboardButton
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("Опубликовать в VK", callback_data=str(id))
            markup.add(button)

            # Отправка заголовка и текста новости пользователю
            try:
                await bot.send_message(chat_id, f"{title}\n\n{text}", reply_markup=markup)
            except BotBlocked:
                print(f"Пользователь заблокировал бота: {chat_id}")

            # Если найдена ссылка на медиа
            if media_url:
                # Отправка медиа пользователю
                try:
                    await bot.send_photo(chat_id, photo=media_url)
                except Exception as e:
                    print(f"Ошибка при отправке фото: {e}")
    else:
        await bot.send_message(chat_id, "Новые новости не найдены")


async def on_shutdown(dp):
    # Закрытие соединения с базой данных (если используется)
    await bot.send_message(chat_id, 'Бот был остановлен')
    await dp.storage.close()
    await dp.storage.wait_closed()


async def upload_video(id):
    vk = vk_api.get_api()

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    # Получение имени файла видео из базы данных
    c.execute("SELECT video_filename FROM news WHERE id = ?", (id,))
    video_filename = c.fetchone()[0]

    # Закрытие соединения с базой данных
    conn.close()

    # Проверка наличия видеофайла
    if not os.path.isfile(f"video/{video_filename}"):
        print("Видеофайл не найден")
        return False

    try:
        # Загрузка видео на стену
        video_file_path = f"video/{video_filename}"
        response = vk.video.save(group_id=212791279, wallpost=1, link=video_file_path)
        video_id = response['video_id']
        owner_id = response['owner_id']

        # Публикация видео на стене
        vk.wall.post(owner_id=212791279, from_group=1, attachments=f'video{owner_id}_{video_id}')

        return True
    except Exception as e:
        print(f"Ошибка при загрузке видео: {e}")
        return False


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)