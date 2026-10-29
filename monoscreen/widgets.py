"""Dokunmatik uyumlu bileşenler ve uygulama döngüsü."""
import time
from typing import Callable, List, Optional

from .screen import Screen
from .terminal import Event, Terminal


class Widget:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.visible = True

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h

    def draw(self, screen: Screen):  # pragma: no cover
        pass

    def handle(self, ev: Event) -> bool:
        return False


class Label(Widget):
    def __init__(self, x: int, y: int, text: str, bold: bool = False, inv: bool = False):
        super().__init__(x, y, len(text), 1)
        self.text, self.bold, self.inv = text, bold, inv

    def draw(self, screen):
        self.w = len(self.text)
        screen.put(self.x, self.y, self.text, inv=self.inv, bold=self.bold)


class Button(Widget):
    """Parmak için en az 3 satır yükseklik önerilir. Basılıyken renkler ters döner."""

    def __init__(self, x, y, w, h, text, on_click: Optional[Callable[["Button"], None]] = None):
        super().__init__(x, y, w, h)
        self.text, self.on_click, self.pressed = text, on_click, False

    def draw(self, screen):
        inv = self.pressed
        screen.fill(self.x, self.y, self.w, self.h, inv=inv)
        if self.h >= 3:
            screen.box(self.x, self.y, self.w, self.h, "round", inv=inv)
        tx = self.x + (self.w - len(self.text)) // 2
        screen.put(tx, self.y + self.h // 2, self.text[: self.w], inv=inv, bold=True)

    def handle(self, ev):
        if ev.kind != "mouse":
            return False
        inside = self.contains(ev.x, ev.y)
        if ev.action == "down" and inside:
            self.pressed = True
            return True
        if ev.action == "drag" and self.pressed:
            self.pressed = inside
            return True
        if ev.action == "up" and self.pressed:
            self.pressed = False
            if inside and self.on_click:
                self.on_click(self)
            return True
        return False


class Checkbox(Widget):
    def __init__(self, x, y, text, checked=False, on_change: Optional[Callable[[bool], None]] = None):
        super().__init__(x, y, len(text) + 4, 1)
        self.text, self.checked, self.on_change = text, checked, on_change

    def draw(self, screen):
        screen.put(self.x, self.y, ("[x] " if self.checked else "[ ] ") + self.text)

    def handle(self, ev):
        if ev.kind == "mouse" and ev.action == "down" and self.contains(ev.x, ev.y):
            self.checked = not self.checked
            if self.on_change:
                self.on_change(self.checked)
            return True
        return False


class Slider(Widget):
    """Sürükle: 0.0 - 1.0 arası değer."""

    def __init__(self, x, y, w, value=0.5, on_change: Optional[Callable[[float], None]] = None):
        super().__init__(x, y, w, 1)
        self.value, self.on_change, self.active = value, on_change, False

    def draw(self, screen):
        pos = int(self.value * (self.w - 1))
        screen.put(self.x, self.y, "─" * self.w)
        screen.put(self.x + pos, self.y, "█", bold=True)

    def _set(self, px):
        self.value = min(1.0, max(0.0, (px - self.x) / max(1, self.w - 1)))
        if self.on_change:
            self.on_change(self.value)

    def handle(self, ev):
        if ev.kind != "mouse":
            return False
        if ev.action == "down" and self.contains(ev.x, ev.y):
            self.active = True
            self._set(ev.x)
            return True
        if ev.action == "drag" and self.active:
            self._set(ev.x)
            return True
        if ev.action == "up" and self.active:
            self.active = False
            return True
        return False


class App:
    """Ana döngü. Alt sınıfla ya da callback'lerle kullanılır.

        app = App()
        app.add(Button(2, 2, 12, 3, "Tamam", lambda b: app.quit()))
        app.run()
    """

    def __init__(self, fps: int = 30):
        self.widgets: List[Widget] = []
        self.fps = fps
        self.running = False
        self.screen: Optional[Screen] = None
        self.on_key: Optional[Callable[[Event], None]] = None
        self.on_mouse: Optional[Callable[[Event], None]] = None
        self.on_draw: Optional[Callable[[Screen], None]] = None
        self.on_tick: Optional[Callable[[float], None]] = None

    def add(self, widget: Widget) -> Widget:
        self.widgets.append(widget)
        return widget

    def quit(self):
        self.running = False

    def dispatch(self, ev: Event):
        if ev.kind == "mouse":
            for w in reversed(self.widgets):
                if w.visible and w.handle(ev):
                    return
            if self.on_mouse:
                self.on_mouse(ev)
        elif ev.kind == "key":
            if ev.key in ("ctrl-c", "q") and self.on_key is None:
                self.quit()
                return
            for w in reversed(self.widgets):
                if w.visible and w.handle(ev):
                    return
            if self.on_key:
                self.on_key(ev)

    def draw(self):
        self.screen.clear()
        if self.on_draw:
            self.on_draw(self.screen)
        for w in self.widgets:
            if w.visible:
                w.draw(self.screen)

    def run(self):
        self.running = True
        with Terminal() as term:
            self.screen = Screen(*term.size())
            last = time.time()
            force = True
            while self.running:
                for ev in term.poll(1.0 / self.fps):
                    if ev.kind == "resize":
                        self.screen.resize(*term.size())
                        force = True
                    else:
                        if ev.kind == "key" and ev.key == "ctrl-c":
                            self.quit()
                        self.dispatch(ev)
                now = time.time()
                if self.on_tick:
                    self.on_tick(now - last)
                last = now
                self.draw()
                self.screen.flush(term, force)
                force = False
