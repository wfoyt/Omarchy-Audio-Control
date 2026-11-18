import base64
import importlib.util
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('artwork_loader', ROOT / 'artwork_loader.py')
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


class ArtworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.cover = self.dir / 'cover space %.png'
        self.cover.write_bytes((ROOT / 'preview.png').read_bytes())

    def run_reader(self, url):
        result = subprocess.run(['/usr/bin/python3', '-I', str(ROOT / 'artwork_loader.py'), url],
                                capture_output=True, timeout=4)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b'')
        return result.stdout

    def test_valid_image_and_encoded_filename(self):
        result = self.run_reader(self.cover.as_uri())
        self.assertTrue(result.startswith(b'data:image/png;base64,'))
        self.assertEqual(base64.b64decode(result.split(b',')[1]), self.cover.read_bytes())

    def test_valid_jpeg(self):
        result = self.run_reader((ROOT / "tests/fixtures/cover.jpg").as_uri())
        self.assertTrue(result.startswith(b"data:image/jpeg;base64,"))

    def test_nonregular_files_do_not_block(self):
        fifo = self.dir / 'pipe.png'
        os.mkfifo(fifo)
        sockpath = self.dir / 'socket.png'
        with socket.socket(socket.AF_UNIX) as sock:
            sock.bind(str(sockpath))
            for path in [fifo, sockpath, self.dir, Path('/dev/zero'), Path('/dev/random'), Path('/proc/self/status')]:
                with self.subTest(path=path):
                    self.assertEqual(self.run_reader(path.as_uri()), b'')

    def test_symlinks_followed_only_to_regular_files(self):
        link = self.dir / 'link'
        link.symlink_to(self.cover)
        self.assertTrue(self.run_reader(link.as_uri()))
        link.unlink()
        link.symlink_to('/dev/zero')
        self.assertEqual(self.run_reader(link.as_uri()), b'')

    def test_path_replacement_cannot_change_vetted_inode(self):
        real_open = os.open
        original = self.cover.read_bytes()
        def swap(path, flags):
            if str(path).startswith('/proc/self/fd/'):
                self.cover.unlink()
                os.mkfifo(self.cover)
            return real_open(path, flags)
        with patch.object(loader.os, 'open', side_effect=swap):
            self.assertEqual(loader.read_regular(str(self.cover)), original)

    def test_oversized_empty_missing_and_nonimage(self):
        for content in [b'', b'<svg><image href="https://example.invalid"/></svg>', b'not an image']:
            self.cover.write_bytes(content)
            self.assertEqual(self.run_reader(self.cover.as_uri()), b'')
        with self.cover.open('wb') as stream:
            stream.truncate(loader.MAX_BYTES + 1)
        self.assertEqual(self.run_reader(self.cover.as_uri()), b'')
        self.cover.unlink()
        self.assertEqual(self.run_reader(self.cover.as_uri()), b'')

    def test_byte_limit_even_when_file_grows(self):
        self.cover.write_bytes(b'x' * 20)
        with patch.object(loader, 'MAX_BYTES', 10), patch.object(loader.os, 'fstat') as info:
            info.return_value = os.stat(ROOT / 'preview.png')
            info.return_value = type('Stat', (), {'st_mode': 0o100600, 'st_size': 1, 'st_dev': 1, 'st_ino': 1})()
            with self.assertRaises(ValueError):
                loader.read_regular(str(self.cover))

    def test_network_and_malformed_urls(self):
        for url in ['https://127.0.0.1/a', 'http://192.168.1.1/a', 'file://localhost/etc/passwd',
                    '//example.com/a', 'file:relative', 'file:////example.com/a',
                    'file:///%2fexample.com/a', 'file:///a%00', 'file:///a%0a', 'file:///a%ZZ',
                    'file:///a?x', 'file:///a#x', 'data:image/png;base64,xxx']:
            with self.subTest(url=url):
                self.assertEqual(self.run_reader(url), b'')

    def test_dimensions_and_malformed_headers(self):
        png = self.cover.read_bytes()
        self.assertEqual(loader.image_type(png), 'image/png')
        for data in [png[:10], png[:16] + struct.pack('>II', 8193, 2) + png[24:],
                     png[:16] + struct.pack('>II', 8192, 8192) + png[24:],
                     b'\xff\xd8\xff', b'\xff\xd8\xff\xc0\x00\x01']:
            with self.assertRaises((ValueError, IndexError)):
                loader.image_type(data)
        jpeg = b'\xff\xd8\xff\xc0\x00\x0b\x08\x00\x10\x00\x20\x01\x01\x11\x00'
        self.assertEqual(loader.image_type(jpeg), 'image/jpeg')


if __name__ == '__main__':
    unittest.main()
