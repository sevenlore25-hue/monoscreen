import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from monoscreen import Button, Canvas, Checkbox, Screen, Slider, parse
from monoscreen.terminal import Event


class ParseTests(unittest.TestCase):
    def test_touch_down_up(self):
        evs = parse(b"\x1b[<0;11;6M\x1b[<0;11;6m")
        self.assertEqual([(e.action, e.x, e.y) for e in evs], [("down", 10, 5), ("up", 10, 5)])

    def test_drag_and_scroll(self):
        evs = parse(b"\x1b[<32;3;4M\x1b[<64;1;1M\x1b[<65;1;1M")
        self.assertEqual([e.action for e in evs], ["drag", "scroll_up", "scroll_down"])

    def test_keys(self):
        evs = parse(b"q\x1b[A\r\xc3\xbc")
        self.assertEqual([e.key for e in evs], ["q", "up", "enter", "ü"])


class ScreenTests(unittest.TestCase):
    def test_put_and_clip(self):
        s = Screen(5, 2)
        s.put(3, 0, "abcdef")
        s.put(0, 5, "x")
        self.assertEqual(s.text_dump().split("\n")[0], "   ab")

    def test_diff_render(self):
        s = Screen(4, 2)
        first = s.render()
        self.assertIn("\x1b[1;1H", first)
        self.assertEqual(s.render(), "")
        s.put(0, 1, "a")
        out = s.render()
        self.assertIn("\x1b[2;1H", out)
        self.assertNotIn("\x1b[1;1H", out)

    def test_inverse(self):
        s = Screen(2, 1)
        s.put(0, 0, "a", inv=True)
        self.assertIn("\x1b[0;7m", s.render())


class CanvasTests(unittest.TestCase):
    def test_braille(self):
        c = Canvas(1, 1)
        self.assertEqual(c.cell_char(0, 0), "⠀")
        c.set(0, 0)
        self.assertEqual(c.cell_char(0, 0), "⠁")
        c.rect(0, 0, 2, 4, fill=True)
        self.assertEqual(c.cell_char(0, 0), "⣿")


class WidgetTests(unittest.TestCase):
    def test_button_tap(self):
        hits = []
        b = Button(2, 2, 10, 3, "ok", lambda w: hits.append(1))
        b.handle(Event("mouse", x=3, y=3, action="down"))
        b.handle(Event("mouse", x=3, y=3, action="up"))
        self.assertEqual(hits, [1])

    def test_button_drag_off_cancels(self):
        hits = []
        b = Button(2, 2, 10, 3, "ok", lambda w: hits.append(1))
        b.handle(Event("mouse", x=3, y=3, action="down"))
        b.handle(Event("mouse", x=30, y=30, action="drag"))
        b.handle(Event("mouse", x=30, y=30, action="up"))
        self.assertEqual(hits, [])

    def test_checkbox_and_slider(self):
        c = Checkbox(0, 0, "a")
        c.handle(Event("mouse", x=0, y=0, action="down"))
        self.assertTrue(c.checked)
        s = Slider(0, 0, 11, 0.0)
        s.handle(Event("mouse", x=5, y=0, action="down"))
        self.assertAlmostEqual(s.value, 0.5)


if __name__ == "__main__":
    unittest.main()
