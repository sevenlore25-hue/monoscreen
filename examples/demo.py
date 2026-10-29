"""Demo: düğme, onay kutusu, kaydırıcı ve parmakla çizim tuvali.

Çalıştır:  python examples/demo.py     (çıkış: q veya Ctrl-C)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from monoscreen import App, Button, Canvas, Checkbox, Label, Slider

app = App()
status = Label(2, 1, "Dokun!", bold=True)
app.add(status)

counter = {"n": 0}


def on_click(btn):
    counter["n"] += 1
    status.text = f"Tıklama sayısı: {counter['n']}"


app.add(Button(2, 3, 16, 3, "Tıkla", on_click))
app.add(Button(20, 3, 16, 3, "Temizle", lambda b: canvas.clear()))
app.add(Checkbox(2, 7, "Çizim açık", True))
slider_label = app.add(Label(2, 9, "Fırça: 1"))
brush = {"r": 1}


def on_slide(v):
    brush["r"] = 1 + int(v * 4)
    slider_label.text = f"Fırça: {brush['r']}"


app.add(Slider(2, 10, 30, 0.0, on_slide))

canvas = Canvas(40, 10)
CANVAS_X, CANVAS_Y = 2, 12
state = {"last": None}


def on_mouse(ev):
    if ev.action in ("down", "drag"):
        px, py = canvas.to_pixel(ev.x, ev.y, CANVAS_X, CANVAS_Y)
        if 0 <= px < canvas.pw and 0 <= py < canvas.ph:
            if state["last"] and ev.action == "drag":
                canvas.line(*state["last"], px, py)
            for dx in range(-brush["r"] + 1, brush["r"]):
                for dy in range(-brush["r"] + 1, brush["r"]):
                    canvas.set(px + dx, py + dy)
            state["last"] = (px, py)
    else:
        state["last"] = None


def on_draw(screen):
    screen.box(CANVAS_X - 1, CANVAS_Y - 1, canvas.cols + 2, canvas.rows + 2)
    canvas.draw(screen, CANVAS_X, CANVAS_Y)


app.on_mouse = on_mouse
app.on_draw = on_draw
app.run()
