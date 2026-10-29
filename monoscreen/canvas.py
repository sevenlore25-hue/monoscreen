"""Braille tabanlı piksel tuvali: hücre başına 2x4 siyah/beyaz nokta."""
_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))


class Canvas:
    def __init__(self, cols: int, rows: int):
        self.cols, self.rows = cols, rows
        self.pw, self.ph = cols * 2, rows * 4
        self.buf = [[False] * self.pw for _ in range(self.ph)]

    def clear(self):
        for row in self.buf:
            for i in range(self.pw):
                row[i] = False

    def set(self, x: int, y: int, on: bool = True):
        if 0 <= x < self.pw and 0 <= y < self.ph:
            self.buf[y][x] = on

    def get(self, x: int, y: int) -> bool:
        return 0 <= x < self.pw and 0 <= y < self.ph and self.buf[y][x]

    def line(self, x0, y0, x1, y1, on: bool = True):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, on)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def rect(self, x, y, w, h, fill: bool = False, on: bool = True):
        if fill:
            for j in range(y, y + h):
                for i in range(x, x + w):
                    self.set(i, j, on)
        else:
            self.line(x, y, x + w - 1, y, on)
            self.line(x, y + h - 1, x + w - 1, y + h - 1, on)
            self.line(x, y, x, y + h - 1, on)
            self.line(x + w - 1, y, x + w - 1, y + h - 1, on)

    def circle(self, cx, cy, r, on: bool = True):
        x, y, err = r, 0, 1 - r
        while x >= y:
            for px, py in ((x, y), (y, x), (-y, x), (-x, y), (-x, -y), (-y, -x), (y, -x), (x, -y)):
                self.set(cx + px, cy + py, on)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    def cell_char(self, col: int, row: int) -> str:
        bits = 0
        for j in range(4):
            for i in range(2):
                if self.buf[row * 4 + j][col * 2 + i]:
                    bits |= _BITS[j][i]
        return chr(0x2800 + bits)

    def draw(self, screen, x: int, y: int):
        for r in range(self.rows):
            screen.put(x, y + r, "".join(self.cell_char(c, r) for c in range(self.cols)))

    def to_pixel(self, mouse_x: int, mouse_y: int, origin_x: int = 0, origin_y: int = 0):
        """Hücre koordinatını (dokunma) tuval pikseline çevirir (hücrenin sol üstü)."""
        return (mouse_x - origin_x) * 2, (mouse_y - origin_y) * 4
