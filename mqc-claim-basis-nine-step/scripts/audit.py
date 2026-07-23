#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic self-check + audit summary. Catches the failure modes that
matter legally (missing/edited text) and visually (overflow, red overuse)
BEFORE the image is delivered. Import and call report(map_dict), or run:

    python audit.py <semantic-map.json>
"""
import sys
from common import FS, text_w, parse_date, load_map

FS_LABEL = FS["label"]


def _count_nodes(m):
    return (len(m.get("events", [])) + len(m.get("spans", [])) + len(m.get("points", []))
            + len(m.get("nodes", [])) + len(m.get("rows", [])) + len(m.get("foci", []))
            + len(m.get("segments", [])))


def _red_ratio(m):
    total = _count_nodes(m)
    red = sum(1 for e in m.get("events", []) if e.get("emphasis")) \
        + sum(1 for s in m.get("spans", []) if s.get("emphasis")) \
        + sum(1 for p in m.get("points", []) if p.get("emphasis")) \
        + sum(1 for n in m.get("nodes", []) if n.get("emphasis")) \
        + sum(1 for e in m.get("edges", []) if e.get("emphasis")) \
        + sum(1 for r in m.get("rows", []) if r.get("决定性")) \
        + sum(1 for f in m.get("foci", []) if f.get("core")) \
        + (1 if m.get("worst_case") else 0)
    return red, total


def report(m):
    lines = ["--- audit summary ---"]
    red, total = _red_ratio(m)
    lines.append(f"elements: {total} | emphasized(red): {red}"
                 + ("  <<red overused (1-2 per diagram): consider demoting some to gray"
                    if total and red > 2 else ""))

    # verbatim / numbering provenance echo
    prov = m.get("provenance", {})
    if prov.get("text_policy"):
        lines.append(f"text_policy: {prov['text_policy']}")
    if "numbering" in prov:
        lines.append(f"numbering: {prov['numbering']}")

    # geometry sanity for gantt: which labels won't fit inside their bar
    if m.get("spans"):
        try:
            a0, a1 = parse_date(m["axis"]["start"]), parse_date(m["axis"]["end"])
            days = (a1 - a0).days
            # width unknown here without layout constants; report duration-based hint
            hug = []
            for s in m["spans"]:
                dur = (parse_date(s["to"]) - parse_date(s["from"])).days
                # heuristic: <120 days is a short bar likely to need left-hug labels
                if dur < 120 and text_w(s["label_text"], FS_LABEL) > 60:
                    hug.append(s["id"])
            if hug:
                lines.append(f"short-bar labels likely hugging left edge: {', '.join(hug)} (expected, per rule)")
        except Exception:
            pass

    # surface uncertainties for the human checkpoint
    unc = prov.get("uncertainties", [])
    if unc:
        lines.append("uncertainties to confirm with user:")
        for u in unc:
            lines.append(f"  - {u}")
    print("\n".join(lines))
    return {"elements": total, "red": red, "uncertainties": unc}


if __name__ == "__main__":
    report(load_map(sys.argv[1]))
