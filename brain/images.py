"""Remove metadata from images before they go to Claude (Bauplan Gehirn 11.2, Design Gehirn 8).

Phone photos carry more than pixels: EXIF with the place (GPS), time, phone model, XMP, ICC
profiles, comments, and sometimes whole extra images after the end of the file. Only what is
needed to show the picture is kept:

- JPEG: an allowlist. Tables, frame and scan data, a basic JFIF segment (rebuilt without
  thumbnail) and the plain Adobe colour segment are kept. All other APPn segments, comments
  and everything after the end marker are dropped. Reserved or exotic segments are refused.
- PNG: the image chunks IHDR, PLTE, IDAT, IEND and the rendering chunks tRNS, gAMA, cHRM,
  sRGB, sBIT, bKGD, pHYs. Text, EXIF, time, ICC profile, animation and anything after IEND
  are dropped.

Pixel data is copied byte for byte. Other formats and damaged files are refused rather than
passed on, so nothing slips through unchecked. Only the standard library is used.

Dropping EXIF also drops the orientation tag, while the pixels stay as stored. `clean_image`
therefore reads the orientation first and returns it with the cleaned image, so the caller can
turn the picture upright (frames from the phone page are already upright, Bauplan 11.4).
"""

import struct
import zlib
from dataclasses import dataclass

MAX_BYTES = 20 * 1024 * 1024
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_KEEP = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"sBIT", b"bKGD", b"pHYs"}
_JPEG_STANDALONE = {0x01, *range(0xD0, 0xD8)}  # markers without a length field
# Frame, Huffman and arithmetic tables (C0-CF without the reserved C8), scan, quantisation tables,
# number of lines, restart interval, hierarchical progression, expansion (DA-DF).
_JPEG_KEEP = {*range(0xC0, 0xC8), *range(0xC9, 0xD0), *range(0xDA, 0xE0)}
_EXIF_ORIENTATION = 0x0112


class ImageError(ValueError):
    """Unsupported format, damaged file or too large."""


@dataclass(frozen=True)
class CleanImage:
    data: bytes
    media_type: str
    orientation: int  # EXIF orientation of the original, 1 = upright


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


def clean_image(data):
    """Cleaned image with its media type and the orientation read before cleaning."""
    cleaned = strip_metadata(data)
    kind = media_type(data)
    return CleanImage(cleaned, kind, jpeg_orientation(data) if kind == "image/jpeg" else 1)


def jpeg_orientation(data):
    """EXIF orientation 1 to 8 from the first EXIF segment; 1 if there is none or it is unreadable."""
    position = 2
    while position + 4 <= len(data) and data[position] == 0xFF:
        marker = data[position + 1]
        if marker == 0xDA or marker in _JPEG_STANDALONE or marker in (0xD8, 0xD9):
            break
        length = int.from_bytes(data[position + 2 : position + 4], "big")
        payload = data[position + 4 : position + 2 + length]
        if marker == 0xE1 and payload.startswith(b"Exif\x00\x00"):
            return _orientation_from_tiff(payload[6:])
        position += 2 + length
    return 1


def _orientation_from_tiff(tiff):
    try:
        order = {b"MM": ">", b"II": "<"}[tiff[:2]]
        (ifd,) = struct.unpack(order + "I", tiff[4:8])
        (count,) = struct.unpack(order + "H", tiff[ifd : ifd + 2])
        for index in range(count):
            entry = tiff[ifd + 2 + 12 * index : ifd + 14 + 12 * index]
            tag, kind, _ = struct.unpack(order + "HHI", entry[:8])
            if tag == _EXIF_ORIENTATION and kind == 3:
                (value,) = struct.unpack(order + "H", entry[8:10])
                return value if 1 <= value <= 8 else 1
    except (KeyError, struct.error):
        pass
    return 1


def _jfif(segment):
    """A basic JFIF segment without thumbnail, or None if this APP0 is not JFIF."""
    payload = segment[2:]
    if payload[:5] != b"JFIF\x00" or len(payload) < 14:
        return None
    return struct.pack(">H", 16) + payload[:12] + b"\x00\x00"


def _clean_jpeg_segment(marker, segment):
    """Bytes to keep for this segment (without the marker), None to drop it. `segment` starts with its length."""
    if marker in _JPEG_KEEP:
        return segment
    if marker == 0xE0:  # APP0: only JFIF survives, rebuilt without thumbnail or extra bytes
        return _jfif(segment)
    if marker == 0xEE and segment[2:7] == b"Adobe" and len(segment) == 14:  # plain Adobe colour transform
        return segment
    if 0xE1 <= marker <= 0xEF or marker == 0xFE:  # EXIF, XMP, ICC, IPTC, other APPn, comments
        return None
    raise ImageError(f"JPEG mit unbekanntem Segment 0x{marker:02X}, nicht unterstützt")


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
        kept = _clean_jpeg_segment(marker, segment)
        if kept is not None:
            out += bytes((0xFF, marker)) + kept
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
