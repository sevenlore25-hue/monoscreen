"""Siyah-beyaz hücre tamponu. Yalnızca normal / ters (inverse) / kalın nitelikler kullanılır."""
from typing import List, Tuple

Cell = Tuple[str, bool, bool]  # (karakter, ters, kalın)
BLANK: Cell = (" ", False, False)

BOXES = {
    "single": "┌┐└┘─│",
    "double": "╔╗╚╝═║",
    "round": "╭╮╰╯─│",
    "heavy": "┏┓┗┛━┃",
    "ascii": "++++-|",
}


class Screen:
    def __init__(self, width: int, height: int):
        self.resize(width, height)
        self._last: List[str] = []

    def resize(self, width: int, height: int):
        self.width = max(1, width)
        self.height = max(1, height)
        self.cells: List[List[Cell]] = [[BLANK] * self.width for _ in range(self.height)]
        self._last = []

    def clear(self):
        for row in self.cells:
            for i in range(len(row)):
                row[i] = BLANK

    def put(self, x: int, y: int, text: str, inv: bool = False, bold: bool = False):
        if not (0 <= y < self.height):
            return
        for i, ch in enumerate(text):
            cx = x + i
            if 0 <= cx < self.width:
                self.cells[y][cx] = (ch, inv, bold)

    def fill(self, x: int, y: int, w: int, h: int, ch: str = " ", inv: bool = False):
        for j in range(y, y + h):
            self.put(x, j, ch * w, inv=inv)

    def box(self, x: int, y: int, w: int, h: int, style: str = "single", inv: bool = False):
        if w < 2 or h < 2:
            return
        tl, tr, bl, br, hz, vt = BOXES.get(style, BOXES["single"])
        self.put(x, y, tl + hz * (w - 2) + tr, inv)
        self.put(x, y + h - 1, bl + hz * (w - 2) + br, inv)
        for j in range(y + 1, y + h - 1):
            self.put(x, j, vt, inv)
            self.put(x + w - 1, j, vt, inv)

    def hline(self, x: int, y: int, w: int, ch: str = "─"):
        self.put(x, y, ch * w)

    def center(self, y: int, text: str, inv: bool = False, bold: bool = False):
        self.put((self.width - len(text)) // 2, y, text, inv, bold)

    def _render_row(self, row: List[Cell]) -> str:
        out, cur = [], (False, False)
        for ch, inv, bold in row:
            if (inv, bold) != cur:
                codes = ["0"] + (["7"] if inv else []) + (["1"] if bold else [])
                out.append("\x1b[" + ";".join(codes) + "m")
                cur = (inv, bold)
            out.append(ch)
        out.append("\x1b[0m")
        return "".join(out)

    def render(self, force: bool = False) -> str:
        """Yalnızca değişen satırlar için ANSI dizisi üretir."""
        rows = [self._render_row(r) for r in self.cells]
        if force or len(self._last) != len(rows):
            self._last = [None] * len(rows)  # type: ignore
        out = []
        for y, r in enumerate(rows):
            if self._last[y] != r:
                out.append(f"\x1b[{y + 1};1H{r}")
                self._last[y] = r
        return "".join(out)

    def flush(self, term, force: bool = False):
        data = self.render(force)
        if data:
            term.write(data)

    def text_dump(self) -> str:
        """Test/hata ayıklama için düz metin."""
        return "\n".join("".join(c[0] for c in row) for row in self.cells)
