import flet as ft
from tinytag import TinyTag
import sqlite3

from settings import Colors


def get_metadata(file_path):
    """Получение метаданных аудиофайла.

    Функция использует библиотеку 'TinyTag' для извлечения метаданных аудиофайла, таких как исполнитель, альбом и жанр.
    Если извлечение метаданных невозможно, возвращаются значения по умолчанию.

    Args:
        file_path (str): Путь к аудиофайлу.

    Returns:
        dict: Словарь с ключами 'artist', 'album' и 'genre'.
    """
    metadata = {}
    try:
        tag_info = TinyTag.get(file_path)
        metadata["artist"] = tag_info.artist or "Unknown Artist"
        metadata["album"] = tag_info.album or "Unknown Album"
        metadata["genre"] = tag_info.genre or "Unknown Genre"
    except Exception:
        metadata["artist"] = "Unknown Artist"
        metadata["album"] = "Unknown Album"
        metadata["genre"] = "Unknown Genre"
    return metadata


class AudioPlayer:
    """Класс для управления аудиоплеером.

    Этот класс предоставляет функционал для создания элементов управления плеером, загрузки треков и плейлистов из базы данных,
    а также взаимодействия с базой данных для сохранения информации о треках и плейлистах.

    Attributes:
        page (flet.Page): Объект страницы Flet, на которой будет отображаться интерфейс плеера.
    """
    def __init__(self, page):
        """Конструктор класса `AudioPlayer`.
        
        Инициализирует объект плеера, создавая необходимые элементы управления и загружая данные из базы данных.

        Args:
            page (flet.Page): Объект страницы Flet, на которой будет отображаться интерфейс плеера.
        """
        self.page = page
        self.create_control_elements()
        self.load_tracks_from_db()
        self.load_playlists_from_db()

    def create_control_elements(self):
        """Метод создает элементы управления, такие как кнопки, ползунки и текстовые поля, которые используются для управления воспроизведением, выбора файлов, создания и управления плейлистами."""
        self.play_pause_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.toggle_play_pause,
            icon_color=Colors.black,
        )
        self.stop_button = ft.IconButton(
            icon=ft.Icons.STOP,
            on_click=lambda _: self.current_track.release(),
            icon_color=Colors.black,
        )
        self.rewind_back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS,
            on_click=lambda _: self.current_track.seek(
                self.current_track.get_current_position() - 10000
            ),
            icon_color=Colors.black,
        )
        self.rewind_forward_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD_IOS,
            on_click=lambda _: self.current_track.seek(
                self.current_track.get_current_position() + 10000
            ),
            icon_color=Colors.black,
        )
        self.volume_down_button = ft.IconButton(
            icon=ft.Icons.REMOVE,
            on_click=self.volume_down,
            icon_color=Colors.black,
        )
        self.volume_up_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self.volume_up,
            icon_color=Colors.black,
        )
        self.current_text_position = ft.Text(value=None, color=Colors.black)
        self.speed_025 = ft.TextButton("0.25", on_click=self.set_speed_025)
        self.speed_050 = ft.TextButton("0.50", on_click=self.set_speed_050)
        self.speed_075 = ft.TextButton("0.75", on_click=self.set_speed_075)
        self.speed_100 = ft.TextButton("1", on_click=self.set_speed_100)
        self.speed_125 = ft.TextButton("1.25", on_click=self.set_speed_125)
        self.speed_150 = ft.TextButton("1.5", on_click=self.set_speed_150)
        self.speed_175 = ft.TextButton("1.75", on_click=self.set_speed_175)
        self.speed_200 = ft.TextButton("2", on_click=self.set_speed_200)
        self.pick_files_dialog = ft.FilePicker(on_result=self.add_new_track)
        self.page.overlay.append(self.pick_files_dialog)
        self.current_playlist = None
        self.current_state = None
        self.create_playlist_button = ft.ElevatedButton(
            text="Создать плейлист", on_click=self.create_playlist
        )
        self.add_to_playilst_button = ft.ElevatedButton(
            text="Добавить в плейлист", on_click=self.add_to_playlist
        )
        self.remove_from_playlist_button = ft.ElevatedButton(
            text="Удалить из плейлиста",
            on_click=self.remove_from_playlist,
        )
        self.delete_track_button = ft.ElevatedButton(
            text="Удалить трек", on_click=self.delete_track
        )
        self.delete_playlist_button = ft.ElevatedButton(
            text="Удалить плейлист", on_click=self.delete_playlist
        )
        self.rename_playlist_button = ft.TextField(
            label="Новое имя плейлиста:", width=250
        )
        self.rename_confirm_button = ft.ElevatedButton(
            text="Переименовать", on_click=self.rename_playlist
        )
        self.sort_by_artist_button = ft.IconButton(
            ft.Icons.PERSON, on_click=self.sort_by_artist
        )
        self.sort_by_album_button = ft.IconButton(
            ft.Icons.ALBUM, on_click=self.sort_by_album
        )
        self.sort_by_genre_button = ft.IconButton(
            ft.Icons.MUSIC_NOTE, on_click=self.sort_by_genre
        )
        self.update_metadata_button = ft.IconButton(
            ft.Icons.CHECK, on_click=self.update_metadata
        )
        self.current_track = ft.Audio(
            src=" ",
            autoplay=False,
            volume=0.5,
            balance=0,
            playback_rate=1,
            on_state_changed=self.state_changed,
            on_position_changed=self.change_current_text_position,
        )
        self.page.overlay.append(self.current_track)
        self.all_tracks_list = ft.ListView(
            expand=True, height=300, auto_scroll=False, spacing=10, width=100
        )
        self.current_track_list = ft.ListView(
            expand=True, height=300, auto_scroll=False, spacing=10, width=100
        )
        self.playlist_list = ft.ListView(
            expand=True, height=300, auto_scroll=False, spacing=10, width=100
        )
        self.metadata_list = ft.ListView(
            expand=True, height=300, auto_scroll=False, spacing=10, width=100
        )
        self.search_bar = ft.SearchBar(width=300, height=40, bar_hint_text="Поиск")
        self.search_confirm_button = ft.IconButton(
            ft.Icons.SEARCH, on_click=self.search_by_metadata
        )
        self.current_track_source = None
        self.speed_list = ft.Dropdown(
            width=60,
            options=[
                self.speed_025,
                self.speed_050,
                self.speed_075,
                self.speed_100,
                self.speed_125,
                self.speed_150,
                self.speed_175,
                self.speed_200,
            ],
        )
        self.open_file_button = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: self.pick_files_dialog.pick_files(
                        allow_multiple=False
                    ),
                ),
            ],
        )
        self.bottom_app_bar = ft.BottomAppBar(
            bgcolor=Colors.green,
            shape=ft.NotchShape.CIRCULAR,
            height=60,
            content=ft.Row(
                [
                    self.volume_down_button,
                    self.volume_up_button,
                    ft.Container(expand=True),
                    self.rewind_back_button,
                    self.play_pause_button,
                    self.stop_button,
                    self.rewind_forward_button,
                    ft.Container(expand=True),
                    self.current_text_position,
                    self.speed_list,
                ]
            ),
        )
        self.main_panel = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        [
                            self.open_file_button,
                            self.create_playlist_button,
                            self.delete_playlist_button,
                            self.delete_track_button,
                            self.add_to_playilst_button,
                            self.remove_from_playlist_button,
                            self.rename_playlist_button,
                            self.rename_confirm_button,
                            ft.Container(expand=True),
                        ],
                    ),
                ),
                ft.Container(
                    ft.Row(
                        [
                            self.sort_by_artist_button,
                            self.sort_by_album_button,
                            self.sort_by_genre_button,
                            self.search_bar,
                            self.search_confirm_button,
                        ],
                    ),
                ),
                ft.Container(expand=True),
                ft.Row(
                    [
                        self.all_tracks_list,
                        self.current_track_list,
                        self.playlist_list,
                    ],
                ),
                ft.Container(
                    ft.Row([self.metadata_list, self.update_metadata_button]), width=400
                ),
                ft.Container(expand=True),
                self.bottom_app_bar,
            ],
            expand=True,
        )

    def save_metadata_to_db(self, path):
        """Метод извлекает метаданные аудиофайла, такие как исполнитель, альбом и жанр, и сохраняет их в таблицу 'audio_history' в базе данных.

        Args:
            path (str): Путь к аудиофайлу, для которого необходимо сохранить метаданные.
        """
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()
        metadata = get_metadata(path)
        cursor.execute(
            "INSERT OR IGNORE INTO audio_history (path, artist, album, genre) VALUES (?, ?, ?, ?)",
            (path, metadata["artist"], metadata["album"], metadata["genre"]),
        )
        connection.commit()
        connection.close()

    def create_playlist(self, _):
        """Создание нового плейлиста.

        Метод создает новую запись в таблице 'playlists_history' в базе данных, содержащую название нового плейлиста и добавляет трек в интерфейс пользователя.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(id) FROM playlists_history")
        max_playlist_number = cursor.fetchone()[0] or 0
        connection.close()

        playlist_name = f"Плейлист {max_playlist_number + 1}"
        self.new_playlist = ft.TextButton(
            text=playlist_name, on_click=self.open_selected_playlist
        )
        self.playlist_list.controls.append(self.new_playlist)
        self.page.update()
        self.save_playlist_to_db(playlist_name)

    def delete_track(self, _):
        """Метод удаляет указанный трек из таблиц 'audio_history' и 'playlist_tracks' в базе данных, и из интерфейса пользователя.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if not self.current_track.src:
            return

        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM audio_history WHERE path = ?", (self.current_track.src,)
        )
        track_id = cursor.fetchone()[0]

        cursor.execute("DELETE FROM audio_history WHERE id = ?", (track_id,))

        cursor.execute("DELETE FROM playlist_tracks WHERE track_id = ?", (track_id,))

        connection.commit()
        connection.close()

        self.all_tracks_list.controls = [
            control
            for control in self.all_tracks_list.controls
            if control.text
            != self.current_track.src[
                self.current_track.src.rfind("\\")
                + 1 : self.current_track.src.rfind(".")
            ]
        ]
        self.current_track_list.controls = [
            control
            for control in self.current_track_list.controls
            if control.text
            != self.current_track.src[
                self.current_track.src.rfind("\\")
                + 1 : self.current_track.src.rfind(".")
            ]
        ]
        self.page.update()

    def delete_playlist(self, _):
        """Метод удаляет указанный плейлист из таблицы 'playlists_history' в базе данных, удаляет все записи, связанные с ним в таблице 'playlist_tracks' и удаляет плейлист из интерфейса пользователя.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if not self.current_playlist:
            return

        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM playlists_history WHERE playlist_name = ?",
            (self.current_playlist,),
        )
        playlist_id = cursor.fetchone()[0]

        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,)
        )

        cursor.execute("DELETE FROM playlists_history WHERE id = ?", (playlist_id,))

        connection.commit()
        connection.close()

        self.playlist_list.controls = [
            control
            for control in self.playlist_list.controls
            if control.text != self.current_playlist
        ]

        self.page.update()

    def save_playlist_to_db(self, playlist_name):
        """Метод сохраняет новый плейлист в таблице 'playlists_history' в базе данных.

        Args:
            playlist_name (str): Имя плейлиста, который нужно сохранить.
        """
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO playlists_history (playlist_name) VALUES (?)", (playlist_name,)
        )
        connection.commit()
        connection.close()

    def rename_playlist(self, _):
        """Метод изменяет название плейлиста в базе данных.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if not self.current_playlist or not self.rename_playlist_button.value:
            return

        new_name = self.rename_playlist_button.value.strip()

        if not new_name:
            return

        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM playlists_history WHERE playlist_name = ?",
            (self.current_playlist,),
        )
        playlist_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM playlists_history WHERE playlist_name = ?",
            (new_name,),
        )
        count = cursor.fetchone()[0]

        if count != 0:
            return

        cursor.execute(
            "UPDATE playlists_history SET playlist_name = ? WHERE id = ?",
            (new_name, playlist_id),
        )
        connection.commit()
        connection.close()

        for control in self.playlist_list.controls:
            if control.text == self.current_playlist:
                control.text = new_name
                break
        self.page.update()

        self.rename_playlist_button.value = ""

    def add_new_track(self, e):
        """Метод проверяет наличие трека в базе данных, и если его нет, добавляет его в таблицу 'audio_history' и в список всех треков.

        Args:
            e (flet.Event): Событие, содержащее информацию о выбранном файле.
        """
        for file in e.files:
            connection = sqlite3.connect("audio_history.db")
            cursor = connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM audio_history WHERE path=?", (file.path,)
            )
            count = cursor.fetchone()[0]
            connection.close()

            if count != 0:
                return

            filename = file.name[: file.name.rfind(".")]
            new_text_button = ft.TextButton(text=filename)
            new_text_button.on_click = lambda _: self.play_selected_file(
                file.path, "all_tracks_list"
            )
            self.all_tracks_list.controls.append(new_text_button)
            self.page.update()

            self.current_track.src = file.path
            self.save_metadata_to_db(file.path)
            self.current_track.update()

    def update_metadata_list(self):
        """Обновление списка метаданных текущего трека.

        Метод очищает текущий список метаданных и заполняет его актуальными для текущего трека метаданными.
        """
        self.metadata_list.controls.clear()
        if self.current_track.src:
            connection = sqlite3.connect("audio_history.db")
            cursor = connection.cursor()
            cursor.execute(
                "SELECT path, artist, album, genre FROM audio_history WHERE path = ?",
                (self.current_track.src,),
            )
            meta = cursor.fetchall()[0]
            cursor.close()
            self.metadata_list.controls.append(
                ft.TextField(value=f"{meta[0]}", helper_text="Путь")
            )
            self.metadata_list.controls.append(
                ft.TextField(value=f"{meta[1]}", helper_text="Автор")
            )
            self.metadata_list.controls.append(
                ft.TextField(value=f"{meta[2]}", helper_text="Альбом")
            )
            self.metadata_list.controls.append(
                ft.TextField(value=f"{meta[3]}", helper_text="Жанр")
            )
        self.page.update()

    def update_metadata(self, _):
        """Метод извлекает текущие метаданные трека из списка метаданных и обновляет соответствующие записи в базе данных.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE audio_history SET (artist, album, genre) = (?, ?, ?) WHERE path = ?",
            (
                self.metadata_list.controls[1].value,
                self.metadata_list.controls[2].value,
                self.metadata_list.controls[3].value,
                self.metadata_list.controls[0].value,
            ),
        )
        connection.commit()
        connection.close()

        self.update_metadata_list()
        self.page.update()

    def play_selected_file(self, file_path, source):
        """Метод начинает воспроизведение указанного файла, обновляя различные элементы управления и списки треков.

        Args:
            file_path (str): Путь к файлу, который нужно воспроизвести.
            source (str): Источник, откуда был выбран файл (например, "all_tracks_list").
        """
        self.current_track_source = source
        self.current_track.src = file_path
        self.current_track.update()
        self.current_track.play()
        self.play_pause_button.icon = ft.Icons.PAUSE
        self.play_pause_button.update()
        self.update_metadata_list()

    def open_selected_playlist(self, e):
        """Метод открывает выбранный плейлист, заполняя список current_track_list треками из него.

        Args:
            e (flet.Event): Событие, содержащее информацию о выбранном плейлисте.
        """
        self.current_playlist = e.control.text
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM playlists_history WHERE playlist_name = ?",
            (self.current_playlist,),
        )
        playlist_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT ah.path, ah.artist, ah.album, ah.genre
            FROM audio_history ah
            JOIN playlist_tracks pt ON ah.id = pt.track_id
            WHERE pt.playlist_id = ?
            """,
            (playlist_id,),
        )
        tracks = cursor.fetchall()
        connection.close()

        self.current_track_list.controls.clear()

        for track in tracks:
            full_path = track[0]
            filename = full_path[full_path.rfind("\\") + 1 : full_path.rfind(".")]
            new_text_button = ft.TextButton(text=filename)
            new_text_button.on_click = (
                lambda _, full_path=full_path: self.play_selected_file(
                    full_path, "current_track_list"
                )
            )
            self.current_track_list.controls.append(new_text_button)

        self.page.update()

    def load_tracks_from_db(self):
        """Метод загружает все доступные треки из базы данных и добавляет их в список всех треков."""
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM audio_history")
        tracks = cursor.fetchall()
        connection.close()

        for track in tracks:
            full_path = track[1]
            filename = full_path[full_path.rfind("\\") + 1 : full_path.rfind(".")]
            new_text_button = ft.TextButton(text=filename)
            new_text_button.on_click = (
                lambda _, full_path=full_path: self.play_selected_file(
                    full_path, "all_tracks_list"
                )
            )
            self.all_tracks_list.controls.append(new_text_button)

        self.page.update()

    def load_playlists_from_db(self):
        """Метод загружает все доступные плейлисты из базы данных и добавляет их в список плейлистов."""
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM playlists_history")
        playlists = cursor.fetchall()
        connection.close()

        for playlist in playlists:
            playlist_name = playlist[1]
            new_playlist = ft.TextButton(
                text=playlist_name, on_click=self.open_selected_playlist
            )
            self.playlist_list.controls.append(new_playlist)

        self.page.update()

    def add_to_playlist(self, _):
        """Метод добавляет выбранный трек в текущий плейлист.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if not self.current_track.src or not self.current_playlist:
            return

        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM playlists_history WHERE playlist_name = ?",
            (self.current_playlist,),
        )
        playlist_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT id FROM audio_history WHERE path = ?", (self.current_track.src,)
        )
        track_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM playlist_tracks
            WHERE playlist_id = ? AND track_id = ?
            """,
            (playlist_id, track_id),
        )
        count = cursor.fetchone()[0]

        if count != 0:
            return

        cursor.execute(
            "INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)",
            (playlist_id, track_id),
        )
        connection.commit()
        connection.close()

        full_path = self.current_track.src
        filename = full_path[full_path.rfind("\\") + 1 : full_path.rfind(".")]
        new_text_button = ft.TextButton(text=filename)
        new_text_button.on_click = (
            lambda _, full_path=full_path: self.play_selected_file(
                full_path, "current_track_list"
            )
        )
        self.current_track_list.controls.append(new_text_button)
        self.page.update()

    def remove_from_playlist(self, _):
        """Метод удаляет выбранный трек из текущего плейлиста.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if not self.current_track.src or not self.current_playlist:
            return

        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM playlists_history WHERE playlist_name = ?",
            (self.current_playlist,),
        )
        playlist_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT id FROM audio_history WHERE path = ?", (self.current_track.src,)
        )
        track_id = cursor.fetchone()[0]

        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?" "",
            (playlist_id, track_id),
        )
        connection.commit()

        self.current_track_list.controls = [
            control
            for control in self.current_track_list.controls
            if control.text
            != self.current_track.src[
                self.current_track.src.rfind("\\")
                + 1 : self.current_track.src.rfind(".")
            ]
        ]
        self.page.update()
        connection.close()

    def search_by_metadata(self, _):
        """Метод ищет треки в базе данных, соответствующие указанным критериям поиска, и добавляет их в current_track_list.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        search_bar_request = f"%{self.search_bar.value}%"
        connection = sqlite3.connect("audio_history.db")
        cursor = connection.cursor()
        cursor.execute(
            "SELECT path FROM audio_history WHERE artist Like ? OR album LIKE ? or genre LIKE ?",
            (search_bar_request, search_bar_request, search_bar_request),
        )
        tracks = cursor.fetchall()
        connection.close()

        self.current_track_list.controls.clear()
        for track in tracks:
            full_path = track[0]
            filename = full_path[full_path.rfind("\\") + 1 : full_path.rfind(".")]
            new_text_button = ft.TextButton(text=filename)
            new_text_button.on_click = (
                lambda _, full_path=full_path: self.play_selected_file(
                    full_path, "current_track_list"
                )
            )
            self.current_track_list.controls.append(new_text_button)
        self.page.update()

    def sort_by_genre(self, _):
        """Метод передаёт значение 'genre' для функции sort_by_column.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.sort_by_column("genre")

    def sort_by_album(self, _):
        """Метод передаёт значение 'album' для функции sort_by_column.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.sort_by_column("album")

    def sort_by_artist(self, _):
        """Метод передаёт значение 'artist' для функции sort_by_column.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.sort_by_column("artist")

    def sort_by_column(self, column):
        """Метод сортирует треки в списке всех треков по значению указанного столбца и по алфавиту.

        Args:
            column (str): Название столбца, по которому нужно выполнять сортировку.
        """
        conn = sqlite3.connect("audio_history.db")
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT path, artist, album, genre FROM audio_history ORDER BY {column} ASC"
        )
        tracks = cursor.fetchall()
        conn.close()

        self.all_tracks_list.controls.clear()
        for track in tracks:
            full_path = track[0]
            filename = full_path[full_path.rfind("\\") + 1 : full_path.rfind(".")]
            new_text_button = ft.TextButton(text=filename)
            new_text_button.on_click = (
                lambda _, full_path=full_path: self.play_selected_file(
                    full_path, "all_tracks_list"
                )
            )
            self.all_tracks_list.controls.append(new_text_button)
        self.page.update()

    def toggle_play_pause(self, _):
        """Метод меняет состояние кнопки воспроизведения между иконкой Play_Arrow и Pause, соответственно начиная или останавливая воспроизведение.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if not (self.current_state == "playing"):
            self.play_pause_button.icon = ft.Icons.PAUSE
            self.current_track.resume()
        else:
            self.play_pause_button.icon = ft.Icons.PLAY_ARROW
            self.current_track.pause()

        self.play_pause_button.update()

    def state_changed(self, e):
        """Метод отслеживает изменения состояния аудиофайла.

        Args:
            e (flet.Event): Событие, отражающее изменение состояния аудиофайла.
        """
        self.current_state = e.data

    def change_current_text_position(self, e):
        """Метод обновляет текстовый элемент, отображающий текущее время воспроизведения.

        Args:
            event (flet.Event): Событие, содержащее информацию о текущем времени воспроизведения.
        """
        self.current_text_position.value = int(e.data) // 1000
        self.current_text_position.update()

    def set_speed_025(self, _):
        """Метод устанавливает скорость воспроизведения равную x0.25 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 0.25
        self.current_track.update()

    def set_speed_050(self, _):
        """Метод устанавливает скорость воспроизведения равную x0.5 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 0.5
        self.current_track.update()

    def set_speed_075(self, _):
        """Метод устанавливает скорость воспроизведения равную x0.75 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 0.75
        self.current_track.update()

    def set_speed_100(self, _):
        """Метод устанавливает скорость воспроизведения равную x1 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 1
        self.current_track.update()

    def set_speed_125(self, _):
        """Метод устанавливает скорость воспроизведения равную x1.25 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 1.25
        self.current_track.update()

    def set_speed_150(self, _):
        """Метод устанавливает скорость воспроизведения равную x1.5 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 1.5
        self.current_track.update()

    def set_speed_175(self, _):
        """Метод устанавливает скорость воспроизведения равную x1.75 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 1.75
        self.current_track.update()

    def set_speed_200(self, _):
        """Метод устанавливает скорость воспроизведения равную x2 от нормальной.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        self.current_track.playback_rate = 2
        self.current_track.update()

    def volume_down(self, _):
        """Метод уменьшает уровень громкости на 10%.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if self.current_track.volume > 0:
            self.current_track.volume -= 0.1
            self.current_track.update()

    def volume_up(self, _):
        """Метод увеличивает уровень громкости на 10%.

        Args:
            _ (Any): Игнорируемый аргумент
        """
        if self.current_track.volume < 1:
            self.current_track.volume += 0.1
            self.current_track.update()

    def stop(self):
        """Метод останавливает воспроизведение текущего аудиофайла."""
        self.current_track.stop()