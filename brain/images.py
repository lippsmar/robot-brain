"""Remove metadata from images before they go to Claude (Bauplan Gehirn 11.2, Design Gehirn 8).

Phone photos carry more than pixels: EXIF with the place (GPS), time, phone model, XMP, ICC
profiles, comments, and sometimes whole extra images after the end of the file. Only what is
needed to show the picture is kept:

- JPEG: tables, frame and scan data, JFIF and the plain Adobe colour segment. Every other
  APPn segment, comments and everything after the end marker are dropped.
- PNG: the image chunks IHDR, PLTE, IDAT, IEND and the rendering chunks tRNS, gAMA, cHRM,
  sRGB, sBIT, bKGD, pHYs. Text, EXIF, time, ICC profile, animation and anything after IEND
  are dropped.

Pixel data is copied byte for byte. Other formats and damaged files are refused rather than
passed on, so nothing slips through unchecked. Only the standard library is used.
"""

import struct
import zlib

MAX_BYTES = 20 * 1024 * 1024
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_KEEP = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"sBIT", b"bKGD", b"pHYs"}
_JPEG_STANDALONE = {0x01, *range(0xD0, 0xD8)}  # markers without a length field


class ImageError(ValueError):
    """Unsupported format, damaged file or too large."""


def media_type(data):
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(_PNG_SIGNATURE):
        return "image/png"
    raise ImageError("Bildformat nicht unterstützt, erlaubt sind JPEG und PNG")


def strip_metadata(data):
    """Return the image without metadata; raise ImageError for anything else."""
    if len(data) > MAX_BYTES:
        raise ImageError(f"Bild zu groß (mehr als {MAX_BYTES // (1024 * 1024)} MB)")
    if media_type(data) == "image/jpeg":
        return _strip_jpeg(data)
    return _strip_png(data)


def _drop_jpeg_segment(marker, segment):
    """`segment` starts with its two length bytes."""
    if marker == 0xFE:  # comment
        return True
    if marker == 0xE0:  # APP0: keep JFIF, drop JFXX thumbnails and the rest
        return segment[2:7] != b"JFIF\x00"
    if marker == 0xEE:  # APP14: keep only the plain 12-byte Adobe colour transform
        return not (segment[2:7] == b"Adobe" and len(segment) == 14)
    return 0xE1 <= marker <= 0xEF  # APP1 to APP15: EXIF, XMP, ICC, IPTC and others


def _scan_end(data, position):
    """End of compressed image data: the first 0xFF that starts a real marker."""
    while True:
        index = data.find(b"\xff", position)
        if index == -1 or index + 1 >= len(data):
            raise ImageError("JPEG beschädigt: Bilddaten ohne Abschluss")
        following = data[index + 1]
        if following == 0x00 or 0xD0 <= following <= 0xD7:
            position = index + 2  # stuffed byte or restart marker, still image data
        elif following == 0xFF:
            position = index + 1  # fill byte
        else:
            return index


def _strip_jpeg(data):
    out = bytearray(b"\xff\xd8")
    position = 2
    end = len(data)
    while True:
        if position >= end or data[position] != 0xFF:
            raise ImageError("JPEG beschädigt: Marker erwartet")
        while position < end and data[position] == 0xFF:
            position += 1
        if position >= end:
            raise ImageError("JPEG beschädigt: Ende ohne Abschluss")
        marker = data[position]
        position += 1
        if marker == 0xD9:  # end of image; extras behind it are dropped
            out += b"\xff\xd9"
            return bytes(out)
        if marker in _JPEG_STANDALONE:
            out += bytes((0xFF, marker))
            continue
        if marker in (0x00, 0xD8):
            raise ImageError("JPEG beschädigt: unerwarteter Marker")
        if position + 2 > end:
            raise ImageError("JPEG beschädigt: Segmentlänge fehlt")
        length = int.from_bytes(data[position : position + 2], "big")
        if length < 2 or position + length > end:
            raise ImageError("JPEG beschädigt: Segmentlänge passt nicht")
        segment = data[position : position + length]
        position += length
        if not _drop_jpeg_segment(marker, segment):
            out += bytes((0xFF, marker)) + segment
        if marker == 0xDA:  # start of scan: copy the compressed data unchanged
            scan_end = _scan_end(data, position)
            out += data[position:scan_end]
            position = scan_end


def _strip_png(data):
    out = bytearray(_PNG_SIGNATURE)
    position = len(_PNG_SIGNATURE)
    first = True
    while True:
        if position + 12 > len(data):
            raise ImageError("PNG beschädigt: Ende ohne IEND")
        (length,) = struct.unpack(">I", data[position : position + 4])
        kind = data[position + 4 : position + 8]
        stop = position + 12 + length
        if length > 2**31 - 1 or stop > len(data):
            raise ImageError("PNG beschädigt: Blocklänge passt nicht")
        body = data[position + 8 : stop - 4]
        (checksum,) = struct.unpack(">I", data[stop - 4 : stop])
        if zlib.crc32(kind + body) != checksum:
            raise ImageError(f"PNG beschädigt: Prüfsumme von {kind!r} falsch")
        if first and kind != b"IHDR":
            raise ImageError("PNG beschädigt: IHDR fehlt am Anfang")
        first = False
        if kind in _PNG_KEEP:
            out += data[position:stop]
        position = stop
        if kind == b"IEND":
            return bytes(out)
