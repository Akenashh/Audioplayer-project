import flet as ft
import unittest
from unittest.mock import patch, MagicMock
from player import get_metadata, AudioPlayer

class TestGetMetadata(unittest.TestCase):
    
    def test_get_metadata_success(self):
        # Создаем моки для TinyTag.get()
        mock_tag_info = MagicMock()
        mock_tag_info.artist = 'Burzum'
        mock_tag_info.album = 'Filosofem'
        mock_tag_info.genre = 'Black Metal / Dark Ambient'
        
        with patch('player.TinyTag.get', return_value=mock_tag_info):
            result = get_metadata('./music/burzum-dunkelheit.mp3')
            
        self.assertEqual(result['artist'], 'Burzum')
        self.assertEqual(result['album'], 'Filosofem')
        self.assertEqual(result['genre'], 'Black Metal / Dark Ambient')

    def test_get_metadata_failure(self):
        # Тестируем случай, когда возникает исключение
        with patch('player.TinyTag.get', side_effect=Exception):
            result = get_metadata('./music/500-KB-WAV.wav')
            
        self.assertEqual(result['artist'], 'Unknown Artist')
        self.assertEqual(result['album'], 'Unknown Album')
        self.assertEqual(result['genre'], 'Unknown Genre')


class TestAudioPlayer(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.page_mock = MagicMock()
        self.player = AudioPlayer(self.page_mock)

    def test_set_speed_025_positive(self):
        self.player.current_track = MagicMock()

        self.player.set_speed_025(None)

        # Проверяем, что playback_rate был установлен правильно
        self.assertEqual(self.player.current_track.playback_rate, 0.25)
        self.player.current_track.update.assert_called_once_with()

    def test_set_speed_025_negative(self):
        self.player.current_track = None

        with self.assertRaises(AttributeError):
            self.player.set_speed_025(None)

    def test_set_speed_050_positive(self):
        self.player.current_track = MagicMock()

        self.player.set_speed_050(None)

        self.assertEqual(self.player.current_track.playback_rate, 0.5)
        self.player.current_track.update.assert_called_once_with()

    def test_set_speed_050_negative(self):
        self.player.current_track = None

        with self.assertRaises(AttributeError):
            self.player.set_speed_050(None)

    def test_set_speed_075_positive(self):
        self.player.current_track = MagicMock()

        self.player.set_speed_075(None)

        self.assertEqual(self.player.current_track.playback_rate, 0.75)
        self.player.current_track.update.assert_called_once_with()

    def test_set_speed_075_negative(self):
        self.player.current_track = None

        with self.assertRaises(AttributeError):
            self.player.set_speed_075(None)



if __name__ == "__main__":
    unittest.main()