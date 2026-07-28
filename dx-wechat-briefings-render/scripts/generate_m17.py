#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
M17 法律简报卡片生成器
用法: python generate_m17.py <日期 YYYY-MM-DD> [--fallback]
从 full.json 或 briefing.json 生成 8 张 M17 墨水风 PNG。
"""
import json
import re
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone


TEMPLATE_PATH = Path(r"C:\Users\Daniel Xue\.workbuddy\skills\guizang-social-card-skill\assets\template-legal-briefing.html")
RENDER_SCRIPT = Path(r"C:\Users\Daniel Xue\.workbuddy\skills\guizang-social-card-skill\scripts\render_m17.py")
PYTHON_EXE = Path(r"C:\Users\Daniel Xue\.workbuddy\binaries\python\envs\default\Scripts\python.exe")
BASE_DIR = Path(r"D:\workbuddy\briefings")


def load_source(date_str, force_fallback=False):
    """Load m17 cases from full.json primary path or briefing.json fallback."""
    full_path = BASE_DIR / f"{date_str}-full.json"
    briefing_path = BASE_DIR / f"{date_str}-briefing.json"

    if not force_fallback and full_path.exists():
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        m17 = data.get('m17', {})
        cases = m17.get('cases', [])
        if cases:
            print(f"[M17] Primary path: {full_path} ({len(cases)} cases)")
            return 'full', data, cases

    if briefing_path.exists():
        print(f"[M17] Fallback path: {briefing_path}")
        with open(briefing_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return 'briefing', data, None

    raise FileNotFoundError(f"Neither {full_path} nor {briefing_path} found")


def select_articles_briefing(data):
    """Legacy fallback: select 7 articles from briefing.json and compress manually."""
    articles = data.get('articles', [])
    # Pick first 7 by default; caller (AI) should ideally score and select.
    selected = articles[:7]
    return selected


def render_cover(card):
    toc_html = "\n".join(f'          <div>{item}</div>' for item in card["toc"])
    return f'''    <section class="poster xhs" id="{card['id']}">
      <div class="content">
        <div>
          <p class="date">{card['date']}</p>
          <h1 class="h-xl">{card['title']}</h1>
          <p class="subtitle">{card['subtitle']}</p>
        </div>
        <div class="toc">
{toc_html}
        </div>
      </div>
    </section>'''


def render_content(card):
    steps_html = "\n".join(
        f'''          <div class="step">
            <div class="step-nb">{i:02d}</div>
            <div>
              <h3 class="step-title">{step['title']}</h3>
              <p class="step-desc">{step['desc']}</p>
            </div>
          </div>'''
        for i, step in enumerate(card["steps"], 1)
    )
    title_html = card["title"].replace("\n", "<br>")
    advice = card.get("advice", "")
    if advice.startswith("应对建议："):
        advice = advice[5:]
    return f'''    <section class="poster xhs" id="{card['id']}">
      <div class="content stack">
        <div>
          <p class="kicker">{card['kicker']}</p>
          <h2 class="h-xl">{title_html}</h2>
        </div>
        <div class="pipeline-v">
{steps_html}
        </div>
        <p class="body"><strong>应对建议：</strong>{advice}</p>
      </div>
    </section>'''


def build_cards_from_full(full_data, date_str):
    """Build 8 cards from full.json m17.cases."""
    cases = full_data['m17']['cases']
    cover = {
        "id": "xhs-01",
        "date": date_str.replace("-", "."),
        "title": "今日法律观察",
        "subtitle": "Daily Legal Briefing",
        "toc": [f"{c['index']:02d} · {c['title']}" for c in cases],
        "is_cover": True,
    }
    content_cards = []
    for i, c in enumerate(cases, 2):
        steps = [{"title": p["title"], "desc": p["desc"]} for p in c.get("points", [])[:3]]
        # Pad to 3 steps if needed
        while len(steps) < 3:
            steps.append({"title": "要点", "desc": ""})
        content_cards.append({
            "id": f"xhs-{i:02d}",
            "kicker": c.get("kicker", f"案例 {i-1:02d}"),
            "title": c["title"],
            "steps": steps,
            "advice": c.get("advice", ""),
        })
    return [cover] + content_cards


def generate_index_html(cards, output_path):
    body_sections = "\n\n".join(
        render_cover(card) if card.get("is_cover") else render_content(card)
        for card in cards
    )
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    new_html = re.sub(
        r"<body>.*?</body>",
        f"<body>\n  <div class=\"sheet\">\n\n{body_sections}\n\n  </div>\n</body>",
        template,
        flags=re.DOTALL,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"[M17] Generated: {output_path}")


def write_metadata(date_str, source_type, source_path, cards, output_dir):
    meta = {
        "date": date_str,
        "style": "M17 Editorial Magazine × E-ink / Ink Classic",
        "source_type": source_type,
        "source_briefing": str(source_path),
        "skill": "m17-briefing-render",
        "total_cards": len(cards),
        "cards": [
            {
                "id": c["id"],
                "type": "cover" if c.get("is_cover") else "content",
                "title": c.get("title", "今日法律观察"),
                "kicker": c.get("kicker", ""),
                "output": f"{c['id']}.png",
            }
            for c in cards
        ],
        "output_dir": str(output_dir),
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
    }
    meta_path = output_dir / f"{date_str}-m17.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[M17] Metadata: {meta_path}")


def update_full_json_pipeline(date_str):
    full_path = BASE_DIR / f"{date_str}-full.json"
    if full_path.exists():
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data.setdefault('pipeline', {})['part_c_completed'] = True
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[M17] Updated pipeline.part_c_completed in {full_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_m17.py <YYYY-MM-DD> [--fallback]")
        sys.exit(1)

    date_str = sys.argv[1]
    force_fallback = "--fallback" in sys.argv

    output_dir = BASE_DIR / f"{date_str}-m17"
    output_dir.mkdir(parents=True, exist_ok=True)

    source_type, data, cases = load_source(date_str, force_fallback)

    if source_type == 'full' and cases:
        cards = build_cards_from_full(data, date_str)
    else:
        print("[M17] Fallback: AI must manually compress articles from briefing.json")
        # In fallback mode, the caller (AI) is expected to provide compressed content.
        # This script only prepares the structure; the actual compression remains in the skill workflow.
        selected = select_articles_briefing(data)
        # Build minimal cards with raw titles; caller should override.
        cover = {
            "id": "xhs-01",
            "date": date_str.replace("-", "."),
            "title": "今日法律观察",
            "subtitle": "Daily Legal Briefing",
            "toc": [f"{a['index']:02d} · {a['title'][:20]}" for a in selected],
            "is_cover": True,
        }
        cards = [cover]
        for i, a in enumerate(selected, 2):
            cards.append({
                "id": f"xhs-{i:02d}",
                "kicker": f"案例 {i-1:02d}",
                "title": a['title'][:30],
                "steps": [
                    {"title": "核心定性", "desc": "待压缩"},
                    {"title": "法理审视", "desc": "待压缩"},
                    {"title": "实务要点", "desc": "待压缩"},
                ],
                "advice": "应对建议：待压缩",
            })

    index_path = output_dir / "index.html"
    generate_index_html(cards, index_path)

    # Render PNGs via Playwright
    subprocess.run(
        [str(PYTHON_EXE), str(RENDER_SCRIPT), str(output_dir)],
        check=True,
    )

    source_path = BASE_DIR / f"{date_str}-{source_type}.json"
    write_metadata(date_str, source_type, source_path, cards, output_dir)
    update_full_json_pipeline(date_str)

    print(f"[M17] Done. Output: {output_dir}")


if __name__ == "__main__":
    main()
