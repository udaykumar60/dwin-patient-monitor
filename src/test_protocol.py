from src.dgus_protocol import FrameParser, set_page, to_hex, write_curve, write_text, write_words


def test_write_and_page():
    frame = write_words(0x1000, 72)
    assert to_hex(frame) == "5A A5 05 82 10 00 00 48"
    page = set_page(1)
    assert to_hex(page) == "5A A5 07 82 00 84 5A 01 00 01"
    text = write_text(0x1100, "OK", words=4)
    parser = FrameParser()
    frames = parser.feed(text)
    assert len(frames) == 1
    assert frames[0].address == 0x1100
    curve = write_curve(0, [128, 144])
    assert to_hex(curve) == "5A A5 06 84 01 00 80 00 90"


if __name__ == "__main__":
    test_write_and_page()
    print("protocol ok")
