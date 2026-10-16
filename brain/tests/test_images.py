"""Tests for removing image metadata before images go to Claude (Bauplan Gehirn 11.2)."""

import struct
import zlib
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from brain.images import MAX_BYTES, ImageError, clean_image, media_type, strip_metadata

FIXTURES = Path(__file__).with_name("fixtures")
META_JPG = (FIXTURES / "meta.jpg").read_bytes()  # EXIF with GPS, XMP, ICC, comment, data after the end
CLEAN_JPG = (FIXTURES / "clean.jpg").read_bytes()  # the same pixels, saved without metadata
META_PNG = (FIXTURES / "meta.png").read_bytes()  # tEXt, iTXt, zTXt, eXIf, data after the end
TRACES = [b"TestPhone", b"Model 7", b"2026:10:16", b"Frankfurt", b"Marvin", b"xmpmeta", b"ICC_PROFILE", b"TRAILER"]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SOS_HEADER = b"\x01\x01\x00\x00\x3f\x00"


def segment(marker, payload):
    return bytes((0xFF, marker)) + struct.pack(">H", len(payload) + 2) + payload


def jpeg(*segments, scan=b"\x12\xff\x00\x34\xff\xd0\x56", trailer=b""):
    return b"\xff\xd8" + b"".join(segments) + segment(0xDA, SOS_HEADER) + scan + b"\xff\xd9" + trailer


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


IHDR = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
IDAT = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
IEND = chunk(b"IEND", b"")


def png(*chunks, trailer=b""):
    return PNG_SIGNATURE + IHDR + b"".join(chunks) + IDAT + IEND + trailer


def png_chunks(data):
    position, kinds = len(PNG_SIGNATURE), []
    while position < len(data):
        (length,) = struct.unpack(">I", data[position : position + 4])
        kinds.append(data[position + 4 : position + 8])
        position += 12 + length
    return kinds


def test_jpeg_metadata_is_removed():
    cleaned = strip_metadata(META_JPG)

    for trace in TRACES:
        assert trace not in cleaned, trace


def test_jpeg_pixels_are_untouched():
    # The same picture saved without metadata gives exactly the same file after cleaning.
    assert strip_metadata(META_JPG) == strip_metadata(CLEAN_JPG) == CLEAN_JPG


def test_png_metadata_is_removed():
    cleaned = strip_metadata(META_PNG)

    for trace in TRACES:
        assert trace not in cleaned, trace
    assert png_chunks(cleaned)[0] == b"IHDR"
    assert png_chunks(cleaned)[-1] == b"IEND"
    assert not {b"tEXt", b"iTXt", b"zTXt", b"eXIf", b"tIME"} & set(png_chunks(cleaned))


@pytest.mark.parametrize("data", [META_JPG, CLEAN_JPG, META_PNG])
def test_cleaning_twice_changes_nothing(data):
    once = strip_metadata(data)

    assert strip_metadata(once) == once


@pytest.mark.parametrize(("data", "kind"), [(META_JPG, "image/jpeg"), (META_PNG, "image/png")])
def test_media_type(data, kind):
    assert media_type(data) == kind


def test_exif_comments_and_trailing_data_are_dropped_but_tables_and_scan_stay():
    tables = segment(0xDB, b"\x00" + bytes(range(64)))
    original = jpeg(
        segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"),
        segment(0xE1, b"Exif\x00\x00GPS 50.1,8.6"),
        segment(0xFE, b"Kommentar"),
        tables,
        trailer=b"zweites Bild mit EXIF",
    )

    cleaned = strip_metadata(original)

    assert cleaned == jpeg(segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"), tables)


def test_stuffed_bytes_and_restart_markers_in_the_image_data_survive():
    scan = b"\x01\xff\x00\x02\xff\xd3\x03\xff\x00"

    assert strip_metadata(jpeg(scan=scan)) == jpeg(scan=scan)


def test_the_plain_adobe_colour_segment_is_kept_other_app14_data_is_not():
    adobe = segment(0xEE, b"Adobe\x00\x64\x00\x00\x00\x00\x01")

    assert strip_metadata(jpeg(adobe)) == jpeg(adobe)
    assert strip_metadata(jpeg(segment(0xEE, b"Adobe\x00\x64 mit Zusatzdaten"))) == jpeg()


def test_only_jfif_survives_in_app0():
    assert strip_metadata(jpeg(segment(0xE0, b"JFXX\x00\x10 Vorschaubild"))) == jpeg()


def test_png_keeps_image_chunks_and_drops_everything_else():
    keep = [chunk(b"gAMA", b"\x00\x00\xb1\x8f"), chunk(b"pHYs", b"\x00\x00\x0b\x13\x00\x00\x0b\x13\x01")]
    drop = [
        chunk(b"tEXt", b"Author\x00Marvin"),
        chunk(b"eXIf", b"MM\x00*GPS"),
        chunk(b"iCCP", b"Kamera\x00\x00x"),
        chunk(b"acTL", b"\x00\x00\x00\x02\x00\x00\x00\x00"),
    ]

    assert strip_metadata(png(*keep, *drop, trailer=b"Rest")) == png(*keep)


@pytest.mark.parametrize(
    "data",
    [
        b"GIF89a\x01\x00\x01\x00",
        b"RIFF\x00\x00\x00\x00WEBPVP8 ",
        b"\x00\x00\x00\x18ftypheic",
        b"",
        b"\xff",
    ],
)
def test_unknown_formats_are_refused(data):
    with pytest.raises(ImageError):
        strip_metadata(data)


@pytest.mark.parametrize(
    "data",
    [
        META_JPG[:200],
        jpeg()[:-2],  # no end marker
        b"\xff\xd8\xff\xe1\x00\x01",  # segment length below 2
        b"\xff\xd8\xff\xe1\x7f\xff abc",  # segment longer than the file
        b"\xff\xd8\x00\x00",  # garbage where a marker belongs
        b"\xff\xd8\xff\xd8\xff\xd9",  # a second start marker
    ],
)
def test_broken_jpegs_are_refused(data):
    with pytest.raises(ImageError):
        strip_metadata(data)


@pytest.mark.parametrize(
    "data",
    [
        META_PNG[:60],
        PNG_SIGNATURE + IDAT + IHDR + IEND,  # IHDR not first
        PNG_SIGNATURE + IHDR + IDAT,  # no IEND
        png()[:-1],
        PNG_SIGNATURE + IHDR[:-1] + b"\x00" + IDAT + IEND,  # wrong checksum
    ],
)
def test_broken_pngs_are_refused(data):
    with pytest.raises(ImageError):
        strip_metadata(data)


def test_huge_images_are_refused():
    with pytest.raises(ImageError, match="groß"):
        strip_metadata(b"\xff\xd8" + bytes(MAX_BYTES))


# Model-based property: random segment lists, random valid image data, random trailing bytes.
_KEPT = [0xDB, 0xC4, 0xC0, 0xDD]
_DROPPED = [0xE1, 0xE2, 0xED, 0xEF, 0xFE]
_payload = st.binary(max_size=40)
# Entropy-coded data: every 0xFF is followed by 0x00 or a restart marker.
_scan = st.lists(
    st.one_of(
        st.binary(min_size=1, max_size=5).map(lambda b: b.replace(b"\xff", b"")),
        st.sampled_from([b"\xff\x00", b"\xff\xd0", b"\xff\xd7"]),
    ),
    max_size=10,
).map(b"".join)


@settings(max_examples=150, deadline=None)
@given(
    st.lists(st.tuples(st.sampled_from(_KEPT + _DROPPED), _payload), max_size=8),
    _scan,
    st.binary(max_size=20),
)
def test_cleaning_keeps_exactly_the_image_segments(segments, scan, trailer):
    original = jpeg(*(segment(marker, payload) for marker, payload in segments), scan=scan, trailer=trailer)
    expected = jpeg(*(segment(marker, payload) for marker, payload in segments if marker in _KEPT), scan=scan)

    cleaned = strip_metadata(original)

    assert cleaned == expected
    assert strip_metadata(cleaned) == cleaned


def test_a_jfif_thumbnail_and_hidden_bytes_are_removed():
    basic = b"JFIF\x00\x01\x02\x01\x00\x48\x00\x48"
    with_thumbnail = basic + b"\x02\x02" + bytes(12) + b"GPS 50.1,8.6 Marvin"

    cleaned = strip_metadata(jpeg(segment(0xE0, with_thumbnail)))

    assert b"Marvin" not in cleaned
    assert cleaned == jpeg(segment(0xE0, basic + b"\x00\x00"))


@pytest.mark.parametrize("marker", [0x02, 0x50, 0xBF, 0xC8, 0xF0, 0xF7, 0xFD])
def test_unknown_segments_are_refused_instead_of_passed_on(marker):
    with pytest.raises(ImageError, match="unbekannt"):
        strip_metadata(jpeg(segment(marker, b"GPS 50.1,8.6 Marvin")))


def exif(orientation, big_endian=True):
    order = ">" if big_endian else "<"
    header = (b"MM" if big_endian else b"II") + struct.pack(order + "HI", 42, 8)
    entry = struct.pack(order + "HHI", 0x0112, 3, 1) + struct.pack(order + "H", orientation) + b"\x00\x00"
    return b"Exif\x00\x00" + header + struct.pack(order + "H", 1) + entry + struct.pack(order + "I", 0)


@pytest.mark.parametrize("big_endian", [True, False])
def test_the_orientation_is_read_before_the_metadata_goes(big_endian):
    original = jpeg(segment(0xE1, exif(6, big_endian)))

    cleaned = clean_image(original)

    assert cleaned.orientation == 6
    assert cleaned.media_type == "image/jpeg"
    assert cleaned.data == jpeg()


@pytest.mark.parametrize(
    "data",
    [
        jpeg(),
        jpeg(segment(0xE1, b"Exif\x00\x00MM\x00*\x00\x00\x00\xff")),  # IFD offset outside the segment
        jpeg(segment(0xE1, exif(9))),  # not a valid orientation
        jpeg(segment(0xE1, b"http://ns.adobe.com/xap/1.0/\x00<x/>")),
        META_PNG,
    ],
)
def test_without_a_valid_orientation_the_image_counts_as_upright(data):
    assert clean_image(data).orientation == 1
