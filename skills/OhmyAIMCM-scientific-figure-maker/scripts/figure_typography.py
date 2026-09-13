"""Resolve actual figure font faces; do not infer a face from a TTC filename.

No downloads, font extraction, global style changes or manuscript-font changes.
Matplotlib's public get_font/findfont APIs preserve collection face indices on
supported versions. Older backends must fail/choose another face, not claim SC
while actually rendering TC. Font availability is not an aesthetic certificate.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

LATIN = ("Arial", "Helvetica", "Liberation Sans", "Nimbus Sans", "DejaVu Sans")
CJK_SC = ("Noto Sans CJK SC", "Source Han Sans SC", "Heiti SC", "Microsoft YaHei", "PingFang SC")


def font_identity(path):
    from matplotlib import font_manager as fm

    font = fm.get_font(path)  # Do not str()/Path() a FontPath before font loading.
    with Path(path).open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "face_index": getattr(path, "face_index", 0),
            "family": font.family_name, "style": font.style_name,
            "postscript_name": font.postscript_name, "file_sha256": digest}


def _choose(families, sample):
    from matplotlib import font_manager as fm

    for family in families:
        try:
            path = fm.findfont(fm.FontProperties(family=[family], weight="normal", style="normal"),
                               fallback_to_default=False)
            face = fm.get_font(path)
            if face.family_name.casefold() != family.casefold():
                continue
            if any(word in face.style_name.lower() for word in ("bold", "black", "heavy", "italic", "oblique")):
                continue
            if not all(ord(char) in face.get_charmap() for char in sample):
                continue
            # This route exports TrueType PDF text. Avoid silently accepting a
            # CFF/variable collection that this backend may mis-embed as Type 42.
            from fontTools.ttLib import TTFont
            with TTFont(str(path), fontNumber=getattr(path, "face_index", 0), lazy=True) as tt:
                if "glyf" not in tt:
                    continue
            return font_identity(path)
        except (OSError, ValueError, RuntimeError):
            continue
    raise ValueError(f"No verified regular TrueType face for {families}; select a supported local font explicitly")


def resolve_figure_fonts(language="en"):
    """Return scoped rc defaults and an actual file/face receipt, not a font menu."""
    if not isinstance(language, str) or language not in {"en", "en-US", "en-GB", "zh", "zh-CN", "zh-Hans"}:
        raise ValueError("Automatic typography supports English or simplified Chinese; use explicit font overrides otherwise")
    latin = _choose(LATIN, "0123456789xyz%−")
    faces = {"latin": latin}
    families = [latin["family"]]
    if language.startswith("zh"):
        cjk = _choose(CJK_SC, "镜面厚度反射率月份输出")
        faces["cjk"] = cjk
        families.append(cjk["family"])
    rc = {"font.family": families, "font.sans-serif": families,
          "font.weight": "normal", "axes.labelweight": "normal", "axes.titleweight": "normal",
          "mathtext.fontset": "custom", "mathtext.rm": latin["family"],
          "mathtext.it": latin["family"] + ":italic", "mathtext.bf": latin["family"] + ":bold",
          "mathtext.sf": latin["family"], "mathtext.fallback": "stix"}
    return rc, {"language": language, "faces": faces,
                "scope": "defaults_before_explicit_overrides; inspect final PDF",
                "aesthetic_acceptance": "not_assessed"}


def inspect_figure_typography(fig, *, final_width_mm=None):
    """Read-only text/face/scale screening; math and glyph appearance need PDF review."""
    from matplotlib import font_manager as fm
    from matplotlib.text import Text

    fig.canvas.draw()
    width = fig.get_figwidth() * 25.4
    scale = 1 if final_width_mm is None else final_width_mm / width
    if not 0 < scale < float("inf"):
        raise ValueError("final_width_mm must be positive and finite")
    faces, warnings, sizes = {}, [], []
    for item in fig.findobj(Text):
        text = item.get_text()
        if not item.get_visible() or not text.strip():
            continue
        sizes.append(item.get_fontsize() * scale)
        prop = item.get_fontproperties()
        plain = re.sub(r"\$[^$]*\$", "", text)
        if "$" in text and re.search(r"[\u4e00-\u9fff]", plain):
            warnings.append(f"Mixed CJK/math Text may lose glyph fallback; use mixed_textbox: {text}")
        if re.search(r"\b[A-Za-z]_[A-Za-z0-9]+\b", plain):
            warnings.append(f"Literal subscript-like label: {text}")
        paths = [prop.get_file()] if prop.get_file() else []
        if not paths:
            for family in prop.get_family():
                candidate = prop.copy()
                candidate.set_family([family])
                try:
                    paths.append(fm.findfont(candidate, fallback_to_default=False))
                except ValueError:
                    warnings.append(f"Unresolved requested font: {family}")
        for path in paths:
            key = (str(path), getattr(path, "face_index", 0))
            if key not in faces:
                faces[key] = font_identity(path)
            if prop.get_file() and faces[key]["family"].endswith(" TC") and re.search(r"[\u4e00-\u9fff]", plain):
                warnings.append("File-bound TC face in Chinese labels; verify language/collection index")
    return {"font_faces": list(faces.values()), "minimum_final_font_pt": min(sizes) if sizes else None,
            "warnings": sorted(set(warnings)), "math_glyphs_and_visual_quality": "require_final_export_review"}


def mixed_textbox(text, *, fontsize=8.5, color="black"):
    """An OffsetBox for inline CJK + math without sending CJK through MathText.

    Place with AnnotationBbox (including leader arrows) or an anchored offset box.
    Preserves the original text runs; does not interpret or rewrite mathematics.
    """
    from matplotlib.offsetbox import HPacker, TextArea, VPacker

    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be nonempty")
    if text.count("$") % 2:
        raise ValueError("unpaired math delimiters")
    rows = []
    for line in text.splitlines():
        parts = re.split(r"(\$[^$]*\$)", line)
        if any(part.startswith("$") and re.search(r"[\u4e00-\u9fff]", part) for part in parts):
            raise ValueError("keep Chinese prose outside math runs")
        children = [TextArea(part, textprops={"fontsize": fontsize, "color": color})
                    for part in parts if part]
        if children:
            rows.append(HPacker(children=children, align="baseline", pad=0, sep=0))
    return rows[0] if len(rows) == 1 else VPacker(children=rows, align="left", pad=0, sep=2)
