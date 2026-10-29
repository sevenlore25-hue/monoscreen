"""Ham terminal girişi: klavye + dokunma (SGR fare raporlama) ve alternatif ekran."""
import os
import re
import select
import shutil
import signal
import sys
import termios
import tty
from dataclasses import dataclass
from typing import List, Optional

ENTER_SEQ = "\x1b[?1049h\x1b[?25l\x1b[?1000h\x1b[?1002h\x1b[?1006h\x1b[2J"
LEAVE_SEQ = "\x1b[?1006l\x1b[?1002l\x1b[?1000l\x1b[?25h\x1b[?1049l"

_MOUSE_RE = re.compile(rb"\x1b\[<(\d+);(\d+);(\d+)([Mm])")

_KEYS = {
    b"\x1b[A": "up", b"\x1b[B": "down", b"\x1b[C": "right", b"\x1b[D": "left",
    b"\x1bOA": "up", b"\x1bOB": "down", b"\x1bOC": "right", b"\x1bOD": "left",
    b"\x1b[H": "home", b"\x1b[F": "end", b"\x1b[5~": "pgup", b"\x1b[6~": "pgdn",
    b"\r": "enter", b"\n": "enter", b"\t": "tab", b"\x7f": "backspace",
    b"\x08": "backspace", b"\x1b": "esc", b"\x03": "ctrl-c",
}


@dataclass
class Event:
    kind: str                 # "key" | "mouse" | "resize"
    key: str = ""             # key olayı için ad ya da karakter
    x: int = 0                # mouse: 0 tabanlı sütun
    y: int = 0                # mouse: 0 tabanlı satır
    action: str = ""          # mouse: down | up | drag | scroll_up | scroll_down


def parse(data: bytes) -> List[Event]:
    """Bayt dizisini olay listesine çevirir (test edilebilir, terminalden bağımsız)."""
    events: List[Event] = []
    i = 0
    while i < len(data):
        m = _MOUSE_RE.match(data, i)
        if m:
            b, x, y, end = int(m[1]), int(m[2]) - 1, int(m[3]) - 1, m[4]
            if b & 64:
                action = "scroll_up" if (b & 1) == 0 else "scroll_down"
            elif b & 32:
                action = "drag"
            else:
                action = "down" if end == b"M" else "up"
            events.append(Event("mouse", x=x, y=y, action=action))
            i = m.end()
            continue
        for seq in sorted(_KEYS, key=len, reverse=True):
            if data.startswith(seq, i):
                events.append(Event("key", key=_KEYS[seq]))
                i += len(seq)
                break
        else:
            # Kaçış dizisi bilinmiyorsa atla; aksi halde UTF-8 karakter oku
            if data[i] == 0x1B:
                j = i + 1
                while j < len(data) and not (0x40 <= data[j] <= 0x7E and j > i + 1):
                    j += 1
                i = j + 1
                continue
            lead = data[i]
            n = 1 if lead < 0x80 else 2 if lead >> 5 == 0b110 else 3 if lead >> 4 == 0b1110 else 4 if lead >> 3 == 0b11110 else 1
            try:
                events.append(Event("key", key=data[i:i + n].decode("utf-8")))
            except UnicodeDecodeError:
                pass
            i += n
    return events


class Terminal:
    """with Terminal() as t: ... şeklinde kullanılır."""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self._old = None
        self._resized = False

    def __enter__(self):
        self._old = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        self._old_winch = signal.signal(signal.SIGWINCH, self._on_winch)
        self.write(ENTER_SEQ)
        return self

    def __exit__(self, *exc):
        self.write(LEAVE_SEQ)
        signal.signal(signal.SIGWINCH, self._old_winch)
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)

    def _on_winch(self, *_):
        self._resized = True

    @staticmethod
    def size():
        s = shutil.get_terminal_size((80, 24))
        return s.columns, s.lines

    @staticmethod
    def write(text: str):
        sys.stdout.write(text)
        sys.stdout.flush()

    def poll(self, timeout: float = 0.05) -> List[Event]:
        events: List[Event] = []
        if self._resized:
            self._resized = False
            events.append(Event("resize"))
        try:
            ready, _, _ = select.select([self.fd], [], [], timeout)
        except InterruptedError:
            return events
        if ready:
            data = os.read(self.fd, 4096)
            events.extend(parse(data))
        return events
