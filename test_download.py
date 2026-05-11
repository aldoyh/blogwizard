import unittest
import sys
import types
from unittest.mock import patch

if "yt_dlp" not in sys.modules:
    sys.modules["yt_dlp"] = types.SimpleNamespace(YoutubeDL=None)

import download


class FakeYoutubeDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        return self._info

    def prepare_filename(self, info):
        return "/tmp/audio/example.webm"

    def download(self, urls):
        return 0


class DownloadTests(unittest.TestCase):
    def test_extract_filesize_prefers_filesize(self):
        size = download._extract_filesize_bytes({"filesize": 123})
        self.assertEqual(size, 123)

    def test_extract_filesize_uses_approx_when_missing(self):
        size = download._extract_filesize_bytes({"filesize": None, "filesize_approx": 456})
        self.assertEqual(size, 456)

    def test_extract_filesize_returns_zero_for_invalid(self):
        size = download._extract_filesize_bytes({"filesize": "invalid"})
        self.assertEqual(size, 0)

    @patch.object(download.youtube_dl, "YoutubeDL")
    def test_download_returns_mp3_when_filesize_unknown(self, youtube_dl_cls):
        client = FakeYoutubeDL({})
        client._info = {"filesize": None, "title": "example", "ext": "webm"}
        youtube_dl_cls.return_value = client

        result = download.download_video_audio("https://example.com/video")

        self.assertEqual(result, "/tmp/audio/example.mp3")

    @patch.object(download.youtube_dl, "YoutubeDL")
    @patch("download.time.sleep")
    def test_download_raises_for_very_large_file(self, mock_sleep, youtube_dl_cls):
        client = FakeYoutubeDL({})
        client._info = {"filesize": download.LARGER_MAX_FILE_SIZE + 1, "title": "example", "ext": "webm"}
        youtube_dl_cls.return_value = client

        with patch.object(download, "max_retries", 1):
            with self.assertRaises(Exception) as error:
                download.download_video_audio("https://example.com/video")

        self.assertEqual(str(error.exception), download.FILE_TOO_LARGE_MESSAGE)


if __name__ == "__main__":
    unittest.main()
