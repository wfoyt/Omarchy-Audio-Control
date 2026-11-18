"""Bounded Linux regular-file artwork reader. No network or shell execution."""
import base64
import os
import re
import signal
import stat
import struct
import sys
from urllib.parse import unquote, urlsplit

MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 16 * 1024 * 1024


def local_path(url):
    if len(url) > 16384 or re.search(r'[\\\x00-\x1f\x7f]', url):
        raise ValueError('Invalid URL')
    parts = urlsplit(url)
    if parts.scheme.lower() != 'file' or parts.netloc or '?' in url or '#' in url:
        raise ValueError('Not a hostless file URL')
    if not url.lower().startswith('file:///'):
        raise ValueError('Not an absolute file URL')
    if re.search(r'%(?![0-9a-fA-F]{2})', parts.path):
        raise ValueError('Invalid escape')
    path = unquote(parts.path, errors='strict')
    if not path.startswith('/') or path.startswith('//') or re.search(r'[\\\x00-\x1f\x7f]', path):
        raise ValueError('Invalid path')
    return path


def read_regular(path):
    # O_PATH pins the inode without opening a FIFO/device for I/O. Validate
    # that descriptor, then reopen that SAME inode, never the mutable pathname.
    pin = os.open(path, os.O_PATH | os.O_CLOEXEC)
    try:
        info = os.fstat(pin)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES:
            raise ValueError('Not bounded regular artwork')
        fd = os.open('/proc/self/fd/' + str(pin), os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        with os.fdopen(fd, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                raise ValueError('File changed')
            data = stream.read(MAX_BYTES + 1)
        if not data or len(data) > MAX_BYTES:
            raise ValueError('Artwork too large')
        return data
    finally:
        os.close(pin)


def image_type(data):
    # Only raster formats with bounded dimensions. SVG and other resource-
    # referencing formats never reach Qt. Qt still validates the encoded image.
    if data[:16] == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' and len(data) >= 33:
        width, height = struct.unpack('>II', data[16:24])
        mime = 'image/png'
    elif data.startswith(b'\xff\xd8'):
        offset = 2
        while offset < len(data):
            if data[offset] != 255:
                raise ValueError('Invalid JPEG')
            while offset < len(data) and data[offset] == 255:
                offset += 1
            marker = data[offset]
            offset += 1
            if marker in (0, 0xD8, 0xD9, 0xDA):
                raise ValueError('Missing JPEG dimensions')
            size = int.from_bytes(data[offset:offset + 2], 'big')
            if size < 2 or offset + size > len(data):
                raise ValueError('Invalid JPEG segment')
            if marker in (0xC0, 0xC1, 0xC2):
                if size < 8:
                    raise ValueError('Invalid JPEG dimensions')
                height, width = struct.unpack('>HH', data[offset + 3:offset + 7])
                break
            offset += size
        else:
            raise ValueError('Missing JPEG dimensions')
        mime = 'image/jpeg'
    else:
        raise ValueError('Unsupported artwork format')
    if not 0 < width <= 8192 or not 0 < height <= 8192 or width * height > MAX_PIXELS:
        raise ValueError('Artwork dimensions too large')
    return mime


def load(url):
    data = read_regular(local_path(url))
    mime = image_type(data)
    return 'data:' + mime + ';base64,' + base64.b64encode(data).decode('ascii')


if __name__ == '__main__':
    # A stalled filesystem read remains outside the shell's image worker.
    signal.alarm(3)
    try:
        result = load(sys.argv[1]) if len(sys.argv) == 2 else ''
    except (OSError, ValueError, IndexError, struct.error):
        result = ''
    sys.stdout.write(result)
