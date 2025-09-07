from app.services.parser import parse_export_lines


def test_parse_basic_and_multiline():
    lines = [
        "12/06/2024, 21:05 - Me: First line",
        "continued line",
        "12/06/2024, 9:06 PM - Me: Next message",
        "12/06/2024, 21:07 - Messages to this chat are now secured with end-to-end encryption.",
    ]
    msgs = parse_export_lines(lines)
    assert len(msgs) == 3
    assert msgs[0].sender == "Me"
    assert msgs[0].text == "First line\ncontinued line"
    assert msgs[1].sender == "Me" and msgs[1].text == "Next message"
    assert msgs[2].sender is None and "secured" in msgs[2].text


def test_handles_colons_and_unicode():
    lines = [
        "01/01/2024, 08:00 - Me: Note: plan: A → B — Café ☕",
        "01/01/2024, 08:05 - System message without sender",
    ]
    msgs = parse_export_lines(lines)
    assert len(msgs) == 2
    assert msgs[0].sender == "Me"
    assert "plan: A" in msgs[0].text
    assert msgs[1].sender is None


def test_supports_us_format_am_pm():
    lines = [
        "06/12/2024, 9:40 PM - Me: US-style date with AM/PM",
    ]
    msgs = parse_export_lines(lines)
    assert len(msgs) == 1
    assert msgs[0].sender == "Me"
    assert "US-style" in msgs[0].text


def test_auto_detect_dmy_vs_mdy():
    # Mix of MDY and DMY-like headers; detector should pick MDY because b>12 occurs
    lines = [
        "5/7/18, 20:48 - System: start",  # MDY (month=5, day=7)
        "5/12/18, 08:30 - Me: hello",     # MDY (day=12)
    ]
    msgs = parse_export_lines(lines)
    assert len(msgs) == 2
    assert msgs[0].timestamp.month == 5 and msgs[0].timestamp.day == 7
    assert msgs[1].timestamp.month == 5 and msgs[1].timestamp.day == 12


