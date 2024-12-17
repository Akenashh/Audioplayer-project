import unittest
from unittest.mock import MagicMock
from player import AudioPlayer


class TestAudioPlayer(unittest.TestCase):
    def setUp(self):
        self.page_mock = MagicMock()
        self.player = AudioPlayer(MagicMock())

    def test_set_speed_025_positive(self):
        self.player.current_track = MagicMock()
        self.player.set_speed_025(None)
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