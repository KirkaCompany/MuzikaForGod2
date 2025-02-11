import logging
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import ffmpeg
import subprocess
import os
import subprocess

# Обновляем yt-dlp перед запуском
subprocess.run(["pip", "install", "--upgrade", "yt-dlp"])
    # --------------------------
    # Часть для скачивания видео с YouTube с использованием cookies через subprocess
    # --------------------------
video_url = "https://www.youtube.com/watch?v=AykAUJYvW_c"
cookies_file = "cookies.txt"  # Убедитесь, что файл cookies.txt загружен в окружение Render или находится в проекте

command = ["yt-dlp", "--cookies", cookies_file, video_url]

result = subprocess.run(command, capture_output=True, text=True)
if result.returncode != 0:
        print("Ошибка при скачивании:", result.stderr)
else:
        print("Видео успешно скачано!")

    # --------------------------
    # Основная часть кода бота
    # --------------------------

    # Устанавливаем логирование
logging.basicConfig(level=logging.INFO)

    # Токен бота Telegram
TOKEN = "7801480937:AAGYlIyrIITlg00Be2DrIUabUJ_gl11DVNI"

    # Данные для подключения к Spotify API
SPOTIPY_CLIENT_ID = "d31233cbd1604ab8a30e1e6b6bffb17a"
SPOTIPY_CLIENT_SECRET = "2547ed9b43584e658220f9561640d7fe"
SPOTIPY_REDIRECT_URI = "https://replit.com/@hhhhshsbb/MuzikaForGodbot"

    # Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

    # Инициализация Spotify API
client_credentials_manager = SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID, 
        client_secret=SPOTIPY_CLIENT_SECRET
    )
sp = Spotify(client_credentials_manager=client_credentials_manager)

    # Клавиатура
start_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Найти музыку")]],
        resize_keyboard=True
    )

    # Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
        await message.answer(
            "🎶 Привет! Я помогу тебе найти и скачать музыку. Напиши название трека или исполнителя!",
            reply_markup=start_keyboard
        )

    # Обработка текста поиска
@dp.message(lambda message: message.text not in ["🔍 Найти музыку", "/start"])
async def search_music(message: types.Message):
        query = message.text

        # Ищем музыку через Spotify API
        results = sp.search(q=query, limit=1, type='track')

        if not results['tracks']['items']:
            await message.answer("❌ Музыка не найдена. Попробуй другой запрос.")
            return

        track = results['tracks']['items'][0]
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        track_url = track['external_urls']['spotify']
        popularity = track['popularity']
        album_name = track['album']['name']
        release_date = track['album']['release_date']

        response_text = (
            f"🎵 <b>Название:</b> {track_name}\n"
            f"🎤 <b>Исполнитель:</b> {artist_name}\n"
            f"📅 <b>Дата релиза:</b> {release_date}\n"
            f"💿 <b>Альбом:</b> {album_name}\n"
            f"🔥 <b>Популярность:</b> {popularity}/100\n"
        )
        await message.answer(response_text, parse_mode="HTML")

        # Скачиваем музыку с YouTube
        await download_and_send_music(message, f"{artist_name} {track_name}")

    # Функция для скачивания и отправки музыки
async def download_and_send_music(message: types.Message, query: str):
        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'audio_format': 'mp3',  # Явное преобразование в mp3
            'quiet': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'force-ipv4': True,
            'cookiefile': './cookies.txt',
            'nocheckcertificate': True,  # ✅ Отключаем проверку SSL-сертификата
        }

        # Убедимся, что папка для скачивания существует
        download_folder = 'downloads'
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Извлекаем информацию и скачиваем файл по запросу
                info = ydl.extract_info(f"ytsearch:{query}", download=True)
                # Если результат содержит список видео, выбираем первое
                if 'entries' in info:
                    info = info['entries'][0]

                # Получаем путь к скачанному файлу
                downloaded_file = ydl.prepare_filename(info)
                logging.info(f"Файл скачан: {downloaded_file}")

                # Проверяем наличие файла
                if not os.path.exists(downloaded_file):
                    raise FileNotFoundError(f"Файл {downloaded_file} не найден")

                # Конвертируем файл в формат OGG (используем ffmpeg)
                input_filename = downloaded_file
                ogg_filename = "music.ogg"

                # Если конвертируемый файл уже существует, удаляем его
                if os.path.exists(ogg_filename):
                    os.remove(ogg_filename)

                ffmpeg.input(input_filename).output(
                    ogg_filename, format='opus', acodec='libopus', audio_bitrate='64k'
                ).run()

                logging.info(f"Файл успешно конвертирован в OGG: {ogg_filename}")

                if not os.path.exists(ogg_filename):
                    raise FileNotFoundError(f"Конвертированный файл {ogg_filename} не найден")

                # Отправляем голосовое сообщение в Telegram
                await bot.send_voice(message.chat.id, FSInputFile(ogg_filename))

                # Удаляем временные файлы
                os.remove(downloaded_file)
                os.remove(ogg_filename)

            except Exception as e:
                await message.answer("❌ Ошибка при загрузке музыки. Попробуй другой запрос.")
                logging.error(f"Ошибка скачивания или конвертации: {e}")

    # Главная функция для запуска бота
async def main():
        await dp.start_polling(bot)

if __name__ == "__main__":
        asyncio.run(main())
