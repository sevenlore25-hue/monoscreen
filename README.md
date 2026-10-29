# monoscreen

Termux için **siyah-beyaz**, **dokunmatik destekli** terminal ekran kütüphanesi.
Bağımlılık yok, sadece Python 3.8+. Diğer projelerde kütüphane olarak kullanılabilir.

- Dokunma: SGR fare raporlama ile sadece tap kaydırma ve sürukleme yok
- Yalnızca ters renk + kalın ile tek renkli arayüz (pil dostu, her terminalde çalışır)
- Satır bazlı fark çizimi (sadece değişen satırlar yazılır)
- Braille tuval: hücre başına 2x4 piksel (çizgi, dikdörtgen, daire)
- Bileşenler: `Label`, `Button`, `Checkbox`, `Slider`, `App` döngüsü

## Kurulum (Termux)

```sh
pkg install -y git python
git clone https://github.com/sevenlore25-hue/monoscreen.git
cd monoscreen
sh install.sh        # pip install -e . yapar
python examples/demo.py
```

Başka projede kullanmak için (kurulumdan sonra) `from monoscreen import ...` yeterli.
Kurmadan kullanmak istersen klasörü projene kopyala ya da submodule ekle:

```sh
git submodule add https://github.com/sevenlore25-hue/monoscreen.git libs/monoscreen
```

## Hızlı örnek

```python
from monoscreen import App, Button, Label

app = App()
msg = app.add(Label(2, 1, "Merhaba", bold=True))
app.add(Button(2, 3, 16, 3, "Dokun", lambda b: setattr(msg, "text", "Dokundun!")))
app.run()          # q veya Ctrl-C ile çık
```

## Düşük seviye kullanım

```python
from monoscreen import Terminal, Screen, Canvas

with Terminal() as t:
    s = Screen(*t.size())
    s.box(0, 0, s.width, s.height, "double")
    s.center(s.height // 2, " monoscreen ", inv=True)
    s.flush(t, force=True)
    while True:
        for ev in t.poll(0.1):
            if ev.kind == "mouse" and ev.action == "down":
                s.put(ev.x, ev.y, "●")
            elif ev.kind == "key" and ev.key == "q":
                raise SystemExit
        s.flush(t)
```

## API özeti

| Nesne | Açıklama |
|---|---|
| `Event` | `kind` (`key`/`mouse`/`resize`), `key`, `x`, `y`, `action` (`down`/`up`/`drag`/`scroll_up`/`scroll_down`) |
| `Terminal` | Ham mod, alternatif ekran, fare açma/kapama; `poll(timeout)` olay listesi döner |
| `Screen` | `put`, `fill`, `box` (single/double/round/heavy/ascii), `center`, `flush` |
| `Canvas(cols, rows)` | `set`, `line`, `rect`, `circle`, `draw(screen, x, y)`, `to_pixel` |
| `App` | `add(widget)`, `on_key`, `on_mouse`, `on_draw`, `on_tick`, `run()`, `quit()` |

Koordinatlar 0 tabanlıdır (sol üst = 0,0). Parmak için düğmeleri en az 3 satır yüksek tut.

## Notlar

- Dokunma olayları Termux'ta fare raporlaması olarak gelir; Termux:GUI gerekmez.
- Çıkışta terminal otomatik eski haline döner (`with Terminal()` blok sonu).
- Test: `python -m unittest discover -s tests`

## Lisans

MIT
