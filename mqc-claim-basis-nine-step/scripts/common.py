#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared helpers for the litigation-timeline renderers.

Design principle: the model only produces semantic-map.json; ALL spatial
work (coordinates, text wrapping, collision-free packing) happens here in
deterministic code, so output quality does not depend on model strength.
"""
import json, os, html
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOKENS_PATH = os.path.join(_HERE, "..", "assets", "style-tokens.json")

with open(_TOKENS_PATH, encoding="utf-8") as _f:
    TOKENS = json.load(_f)

C = TOKENS["colors"]
FONT = TOKENS["font_stack"]
TITLE_FONT = TOKENS.get("title_font", FONT)
FS = TOKENS["type_scale"]
ARROW = TOKENS["arrow"]
RADIUS = TOKENS["radius"]
DASH = TOKENS["dash"]
STROKE = TOKENS["stroke"]


def arrow_marker(mid, color, size=None, refX=None):
    """Clean isosceles arrowhead at a FIXED pixel size (userSpaceOnUse), so it
    does not balloon with stroke-width. Kept small so the tip never overpowers
    the connector or collides with a node."""
    size = size or ARROW["size"]
    refX = refX or ARROW["refX"]
    return (f'<marker id="{mid}" viewBox="0 0 12 12" refX="{refX}" refY="6" '
            f'markerWidth="{size}" markerHeight="{size}" markerUnits="userSpaceOnUse" '
            f'orient="auto"><path d="{ARROW["path"]}" fill="{color}"/></marker>')


def esc(s: str) -> str:
    """Escape text for inclusion in SVG (keeps real <text>, never paths)."""
    return html.escape(s, quote=True)


def char_w(ch: str, fs: float) -> float:
    """Approximate glyph advance. CJK ~= 1em; latin/digits ~= 0.56em.
    Good enough for wrapping and fit-tests without a font engine."""
    return fs if ord(ch) > 0x2E7F else fs * 0.56


def text_w(s: str, fs: float) -> float:
    return sum(char_w(c, fs) for c in s)


def wrap(text: str, fs: float, max_w: float):
    """Greedy character wrap to a max pixel width. Returns list of lines.
    Verbatim: only inserts line breaks, never edits characters."""
    lines, cur, acc = [], "", 0.0
    for ch in text:
        w = char_w(ch, fs)
        if acc + w > max_w and cur:
            lines.append(cur)
            cur, acc = ch, w
        else:
            cur += ch
            acc += w
    if cur:
        lines.append(cur)
    return lines or [""]


def parse_date(s: str) -> date:
    """Parse 'YYYY/M/D' (single or double digit month/day)."""
    y, m, d = (int(x) for x in s.strip().split("/"))
    return date(y, m, d)


def svg_open(width, height):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" '
            f'height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">'
            f'<style>text{{font-family:{FONT};}}</style>'
            f'<rect width="{int(width)}" height="{int(height)}" fill="{C["bg"]}"/>')


def load_map(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_map(m):
    """Structural pre-flight check with actionable messages. Raises RuntimeError
    listing every problem, so a malformed map fails clearly instead of deep in a
    renderer. Does not touch dates (render_spans checks those)."""
    layout = m.get("layout", "")
    errs = []
    if not m.get("title_text"):
        errs.append('missing "title_text" (chart title)')
    if layout in ("graphviz_flow", "graphviz_relation"):
        nodes = m.get("nodes") or []
        if not nodes:
            errs.append('"nodes" is empty')
        ids = set()
        for i, n in enumerate(nodes):
            nid = n.get("id")
            if not nid:
                errs.append(f"node #{i} has no id")
            if not n.get("title"):
                errs.append(f'node "{nid or i}" has no title')
            ids.add(nid)
        for e in m.get("edges") or []:
            if e.get("from") not in ids or e.get("to") not in ids:
                errs.append(f'edge {e.get("from")}->{e.get("to")} references a missing node id')
    elif layout == "numbered_point_timeline":
        evs = m.get("events") or []
        if not evs:
            errs.append('"events" is empty')
        for i, ev in enumerate(evs):
            if not ev.get("text"):
                errs.append(f"event #{i} has no text")
    elif layout == "proportional_gantt":
        ax = m.get("axis") or {}
        if not ax.get("start") or not ax.get("end"):
            errs.append('"axis" needs start and end')
        if not (m.get("spans") or []):
            errs.append('"spans" is empty')
        for i, s in enumerate(m.get("spans") or []):
            for k in ("from", "to", "label_text"):
                if not s.get(k):
                    errs.append(f'span #{i} missing "{k}"')
    elif layout == "elements_matrix":
        rows = m.get("rows") or []
        if not rows:
            errs.append('"rows" is empty')
        for i, r in enumerate(rows):
            if not r.get("检视项"):
                errs.append(f'row #{i} missing "检视项"')
            if not r.get("步"):
                errs.append(f'row "{r.get("id", i)}" missing "步"')
    elif layout == "issues_focus":
        foci = m.get("foci") or []
        if not foci:
            errs.append('"foci" is empty')
        for i, f in enumerate(foci):
            if not f.get("label"):
                errs.append(f'focus #{i} missing "label"')
            if not (f.get("feeders") or []):
                errs.append(f'focus "{f.get("id", i)}" has no feeders')
            for fd in f.get("feeders") or []:
                if not fd.get("源") or not fd.get("项"):
                    errs.append(f'focus "{f.get("id", i)}" has a feeder missing "源" or "项"')
    elif layout == "outcome_band":
        segs = m.get("segments") or []
        if len(segs) < 2:
            errs.append('"segments" needs at least 2 outcomes')
        if not m.get("most_likely"):
            errs.append('missing "most_likely"')
        if m.get("most_likely") and m.get("most_likely") not in segs:
            errs.append('"most_likely" is not one of "segments"')
        if m.get("worst_case") and m.get("worst_case") not in segs:
            errs.append('"worst_case" is not one of "segments"')
    else:
        errs.append(f'unknown layout "{layout}"')
    if errs:
        raise RuntimeError("semantic map has problems: " + "; ".join(errs))
    return True
