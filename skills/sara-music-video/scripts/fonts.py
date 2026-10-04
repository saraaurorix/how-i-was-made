"""Windows font names -> fonts on this machine.

The scripts in this repo were first written on Windows and ask for fonts by their Windows file names
("C:/Windows/Fonts/bahnschrift.ttf", "consolab.ttf", "seguisb.ttf", "impact.ttf"...). Those fonts are Microsoft's and are
not in this repo. This module finds the closest face on the machine it runs on:

    from fonts import truetype, font_path
    truetype("bahnschrift.ttf", 64, "Bold Condensed")  # a PIL font; replaces ImageFont.truetype + set_variation_by_name
    font_path("consolab.ttf")                          # a one-face font file, for ffmpeg drawtext

Full Windows paths work too; only the file name counts. Lookup order for each name:
  1. the path itself, if it exists (so everything runs unchanged on Windows);
  2. a `fonts/` folder beside this file: put your own font files there, named like the Windows ones, to choose the faces;
  3. the closest macOS built-in (MAC below), nudged up or down by DY so its glyphs land where the Windows face put them:
     the scripts' paddings were tuned by eye on Windows;
  4. the closest common Linux font (LINUX below);
  5. Pillow's built-in font, so a script still runs. Captions will look plainer.
`python fonts.py [out.png]` draws a proof sheet of every mapping on this machine.
"""
import glob
import os
import sys

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, "fonts")
SYS, SUP = "/System/Library/Fonts", "/System/Library/Fonts/Supplemental"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "how-i-was-made-fonts")  # one-face copies of .ttc faces, for ffmpeg

# Windows file -> (Mac file, face style inside a .ttc). Bahnschrift is a variable DIN 1451 on Windows and the scripts
# mostly ask for its condensed instances, which DIN Condensed Bold matches; anything else gets DIN Alternate Bold.
MAC = {
    "bahnschrift.ttf": (f"{SUP}/DIN Condensed Bold.ttf", None),
    "consola.ttf": (f"{SYS}/Menlo.ttc", "Regular"),
    "consolab.ttf": (f"{SYS}/Menlo.ttc", "Bold"),
    "segoeui.ttf": (f"{SYS}/HelveticaNeue.ttc", "Regular"),
    "seguisb.ttf": (f"{SYS}/HelveticaNeue.ttc", "Medium"),  # Segoe Semibold (600) -> Helvetica Neue Medium (500)
    "segoeuib.ttf": (f"{SYS}/HelveticaNeue.ttc", "Bold"),
    "seguisbi.ttf": (f"{SYS}/HelveticaNeue.ttc", "Medium Italic"),
    "seguili.ttf": (f"{SYS}/HelveticaNeue.ttc", "Light Italic"),
    "arial.ttf": (f"{SUP}/Arial.ttf", None),
    "arialbd.ttf": (f"{SUP}/Arial Bold.ttf", None),
    "ariblk.ttf": (f"{SUP}/Arial Black.ttf", None),
    "impact.ttf": (f"{SUP}/Impact.ttf", None),
    "georgiai.ttf": (f"{SUP}/Georgia Italic.ttf", None),
    "timesbd.ttf": (f"{SUP}/Times New Roman Bold.ttf", None),
    "gara.ttf": (f"{SUP}/Hoefler Text.ttc", "Regular"),
}
BAHN_WIDE = (f"{SUP}/DIN Alternate Bold.ttf", None)
# Vertical nudge per Mac file, in em (+ = down), measured by diffing caption PNGs rendered on Windows against the same
# PNGs rendered on a Mac: DIN Condensed sat 0.085 em high, Helvetica Neue 0.10 em high, Menlo (taller caps than
# Consolas) 0.14 em low. Files not listed are the same fonts as on Windows, or were not measured.
DY = {f"{SUP}/DIN Condensed Bold.ttf": 0.085, f"{SYS}/HelveticaNeue.ttc": 0.10, f"{SYS}/Menlo.ttc": -0.14}

# Windows file -> font file names to look for on Linux, best first (DejaVu and Liberation ship with most distributions).
LINUX = {
    "bahnschrift.ttf": ["DejaVuSansCondensed-Bold.ttf", "LiberationSansNarrow-Bold.ttf", "DejaVuSans-Bold.ttf"],
    "consola.ttf": ["DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"],
    "consolab.ttf": ["DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf"],
    "segoeui.ttf": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    "seguisb.ttf": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "segoeuib.ttf": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "seguisbi.ttf": ["DejaVuSans-BoldOblique.ttf", "LiberationSans-BoldItalic.ttf"],
    "seguili.ttf": ["DejaVuSans-Oblique.ttf", "LiberationSans-Italic.ttf"],
    "arial.ttf": ["LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
    "arialbd.ttf": ["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"],
    "ariblk.ttf": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "impact.ttf": ["DejaVuSansCondensed-Bold.ttf", "LiberationSansNarrow-Bold.ttf", "DejaVuSans-Bold.ttf"],
    "georgiai.ttf": ["DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf"],
    "timesbd.ttf": ["LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"],
    "gara.ttf": ["LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"],
}
LINUX_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.join(os.path.expanduser("~"), ".fonts"),
              os.path.join(os.path.expanduser("~"), ".local", "share", "fonts")]
_faces, _linux = {}, {}


class _Nudged(ImageFont.FreeTypeFont):
    """A face drawn `dy` pixels lower: ImageDraw.text pastes getmask2's mask at xy + its offset, so every d.text() moves."""
    dy = 0

    def getmask2(self, *args, **kwargs):
        im, (x, y) = super().getmask2(*args, **kwargs)
        return im, (x, y + self.dy)

    def getbbox(self, *args, **kwargs):
        left, top, right, bottom = super().getbbox(*args, **kwargs)
        return left, top + self.dy, right, bottom + self.dy


def _linux_file(key):
    """The first of LINUX[key] found under the usual Linux font folders, or None."""
    if key not in _linux:
        hit = None
        for want in LINUX.get(key, []):
            for d in LINUX_DIRS:
                found = glob.glob(os.path.join(d, "**", want), recursive=True)
                if found:
                    hit = found[0]
                    break
            if hit:
                break
        _linux[key] = hit
    return _linux[key]


def _source(name, var=None):
    """(path or None, face style or None, whether `var` can be applied) for a Windows font name or path.
    A path of None means: nothing suitable on this machine, use Pillow's built-in font."""
    name = str(name)
    if os.path.exists(name):
        return name, None, True
    base = os.path.basename(name.replace("\\", "/"))
    local = os.path.join(LOCAL, base)
    if os.path.exists(local):
        return local, None, True
    key = base.lower()
    if key in MAC:
        path, style = BAHN_WIDE if key == "bahnschrift.ttf" and var and "condensed" not in var.lower() else MAC[key]
        if os.path.exists(path):
            return path, style, False
    return _linux_file(key), None, False


def _index(path, style):
    """Face index of `style` ("Bold", "Medium Italic"...) inside a .ttc."""
    if (path, style) not in _faces:
        i = 0
        while True:
            try:
                got = ImageFont.truetype(path, 10, index=i).getname()[1]
            except OSError:
                raise FileNotFoundError(f"no {style!r} face in {path}") from None
            if got.lower() == style.lower():
                _faces[path, style] = i
                break
            i += 1
    return _faces[path, style]


def truetype(name, size, var=None):
    """PIL font for a Windows font name, applying `var` only where the file really is that variable font.
    A Mac substitute comes back nudged by DY so it sits where the Windows face did."""
    path, style, variable = _source(name, var)
    if path is None:
        return ImageFont.load_default(size)  # Pillow 10.1 and later: a scalable built-in face
    index = _index(path, style) if style else 0
    if variable or not DY.get(path):
        f = ImageFont.truetype(path, size, index=index)
        if var and variable:
            try:
                f.set_variation_by_name(var)
            except (OSError, ValueError):  # the file in fonts/ is a static face: use it as it is
                pass
        return f
    f = _Nudged(path, size, index=index)
    f.dy = round(DY[path] * size)
    return f


def font_path(name, var=None):
    """A one-face font file for a Windows font name: .ttc faces are copied out once to CACHE (needs fontTools).
    ffmpeg drawtext places the glyphs itself, so the DY nudge can't apply: add DY[mac file] * size to its y by hand if it matters."""
    path, style, _ = _source(name, var)
    if path is None:
        raise FileNotFoundError(f"no font found for {name!r}: put a .ttf with that name in {LOCAL}")
    if not style:
        return path
    out = os.path.join(CACHE, f"{os.path.splitext(os.path.basename(path))[0]}-{style.replace(' ', '')}.ttf")
    if not os.path.exists(out):
        from fontTools.ttLib import TTCollection
        os.makedirs(CACHE, exist_ok=True)
        TTCollection(path).fonts[_index(path, style)].save(out)
    return out


if __name__ == "__main__":
    from PIL import Image, ImageDraw
    rows = [(k, None) for k in MAC] + [("bahnschrift.ttf", "Bold Condensed"), ("bahnschrift.ttf", "SemiBold Condensed")]
    img = Image.new("RGB", (1600, 70 * len(rows) + 20), "white")
    d = ImageDraw.Draw(img)
    label = truetype("arial.ttf", 20)
    for i, (k, var) in enumerate(rows):
        path, style, _ = _source(k, var)
        y = 10 + 70 * i
        d.text((10, y + 18), f"{k}{' / ' + var if var else ''}", fill="black", font=label)
        d.text((360, y + 4), "OUT OF OFFICE · How would you rate 42%?", fill="black", font=truetype(k, 40, var))
        d.text((1180, y + 22), f"{os.path.basename(path) if path else 'Pillow built-in'}{' / ' + style if style else ''}", fill=(120, 120, 120), font=label)
    out = sys.argv[1] if len(sys.argv) > 1 else "fonts_proof.png"
    img.save(out)
    print("wrote", out)
