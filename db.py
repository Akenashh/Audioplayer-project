import sqlite3


def init_db():
    """Инициализация базы данных для хранения истории воспроизведения аудиофайлов и плейлистов.
    
    Эта функция создает три таблицы в базе данных SQLite: audio_history', 'playlists_history' и 'playlist_tracks'.
    Таблица 'audio_history' хранит информацию о треках, включая путь к файлу, исполнителя, альбом и жанр.
    Таблица 'playlists_history' хранит названия созданных плейлистов.
    Таблица 'playlist_tracks' связывает треки с плейлистами.
    """
    conn = sqlite3.connect('audio_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            artist TEXT,
            album TEXT,
            genre TEXT  
        )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_name TEXT
        )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER,
            track_id INTEGER,
            FOREIGN KEY (playlist_id) REFERENCES playlists_history(id),
            FOREIGN KEY (track_id) REFERENCES audio_history(id)
        )''') 
    conn.commit()
    conn.close()
