import flet as ft

from db import init_db
from player import AudioPlayer


def main(page: ft.Page):
    """Функция инициализирует базу данных, создает экземпляр класса 'AudioPlayer' и добавляет созданный интерфейс на страницу.

    Args:
        page (ft.Page): Страница Flet, на которой будет отображен интерфейс плеера.
    """
    page.title = "Flet Audio Player"
    page.theme_mode = "dark"
    init_db()
    player = AudioPlayer(page)
    page.add(player.main_panel)
    page.update()

ft.app(target=main)