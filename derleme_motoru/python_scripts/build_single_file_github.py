import os
import re
import json
import sqlite3

MASTER_MD_PATH = r"D:\fikh_kitap\Camiur_Ruhas_Nihai_Kulliyat.md"
DB_PATH = os.path.join("metadata", "fikh_corpus.db")
OUTPUT_HTML_PATH = r"D:\fikh_kitap\index.html"

def extract_corpus_raw_data(db_path, limit=600):
    print("[*] Ham Fıkıh Kütüphanesi (SQLite) taranıyor...")
    if not os.path.exists(db_path):
        return []
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE metin_orijinal IS NOT NULL AND LENGTH(metin_orijinal) > 50
        LIMIT ?;
    """, (limit,))
    rows = cur.fetchall()
    
    raw_nodes = []
    for r in rows:
        raw_nodes.append({
            "id": r[0], "mezhep": r[1], "muellif": r[2], "eser": r[3],
            "cilt": r[4], "sayfa": r[5], "kitab": r[6], "bab": r[7],
            "metin": r[8][:380].replace("\n", " ") + "..."
        })
    return raw_nodes

def parse_master_manuscript(md_path):
    print("[*] Master Markdown Külliyatı taranıyor...")
    with open(md_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    parts = raw_text.split("# İKİNCİ KISIM: DÖRT MEZHEBİN ÇAĞDAŞ VE KLASİK İTTİFAK KANUNNAMESİ")
    part1_text = parts[0]
    part2_text = parts[1] if len(parts) > 1 else ""

    issue_blocks = re.split(r"(?=# BÖLÜM:)", part1_text)
    issues_list = []

    for block in issue_blocks:
        if not block.strip(): continue
        m_id_match = re.search(r"## MESELE (\d+):\s*(.+)", block)
        if not m_id_match: continue
        
        m_id = int(m_id_match.group(1))
        m_title = m_id_match.group(2).strip()

        chap_match = re.search(r"# BÖLÜM:\s*(.+)", block)
        chap_name = chap_match.group(1).strip() if chap_match else "GENEL"

        ruhsat_hukum, ruhsat_mezhep, ruhsat_guvence = "", "", ""
        r_match = re.search(r"- \*\*Uygulanacak Kolaylık:\*\*\s*(.+)", block)
        if r_match: ruhsat_hukum = r_match.group(1).strip()
        m_match = re.search(r"- \*\*Esas Alınan Mezhep:\*\*\s*(.+)", block)
        if m_match: ruhsat_mezhep = m_match.group(1).strip()
        g_match = re.search(r"- \*\*Sıhhat ve Telfîk Güvencesi:\*\*\s*(.+)", block)
        if g_match: ruhsat_guvence = g_match.group(1).strip()

        def extract_madhab(m_name):
            pat = rf"### \d+\.\s*{m_name} Mezhebi\s*\n- \*\*Hüküm:\*\*\s*(.+?)(?:\n- \*\*Kaynak İbâre:\*\*\s*(.+?))?(?=\n###|\n##|$)"
            found = re.search(pat, block, re.DOTALL)
            if found:
                h = found.group(1).strip() if found.group(1) else ""
                k = found.group(2).strip() if found.group(2) else ""
                return {"hukum": h, "kaynak": k}
            return {"hukum": "", "kaynak": ""}

        issues_list.append({
            "id": m_id,
            "chapter": chap_name,
            "title": m_title,
            "ruhsat": {"hukum": ruhsat_hukum, "mezhep": ruhsat_mezhep, "guvence": ruhsat_guvence},
            "madhabs": {
                "hanefi": extract_madhab("Hanefî"),
                "safii": extract_madhab("Şâfiî"),
                "maliki": extract_madhab("Mâlikî"),
                "hanbeli": extract_madhab("Hanbelî")
            },
            "hilaf": re.search(r"## 3\. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\s*\n([\s\S]*?)(?=\n## 4\.|$)", block).group(1).strip() if re.search(r"## 3\. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\s*\n([\s\S]*?)(?=\n## 4\.|$)", block) else "",
            "telfik": re.search(r"## 4\. TELFÎK DENETİMİ VE FETVÂ\s*\n([\s\S]*?)(?=\n---|$)", block).group(1).strip() if re.search(r"## 4\. TELFÎK DENETİMİ VE FETVÂ\s*\n([\s\S]*?)(?=\n---|$)", block) else ""
        })

    icma_list = []
    if part2_text:
        sections = re.split(r"### BÖLÜM [IVXLCDM]+:\s*", part2_text)
        for sec in sections:
            if not sec.strip(): continue
            lines = sec.strip().split("\n")
            for line in lines[1:]:
                item_match = re.match(r"^(\d+)\.\s*\*\*(.+?):\*\*\s*(.+)", line.strip())
                if item_match:
                    icma_list.append({
                        "id": int(item_match.group(1)),
                        "title": item_match.group(2).strip(),
                        "rule": item_match.group(3).strip()
                    })

    return issues_list, icma_list

def build_clean_html():
    issues, icma = parse_master_manuscript(MASTER_MD_PATH)
    raw_nodes = extract_corpus_raw_data(DB_PATH)

    full_db = {"issues": issues, "icma": icma, "raw_corpus": raw_nodes}
    db_json_safe = json.dumps(full_db, ensure_ascii=False).replace("</script>", "<\\/script>")

    HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB — 3D Fıkıh Kütüphanesi</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Cinzel:wght@500;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Crimson+Pro:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">

<style>
  :root {
    --leather-outer: #30110d;
    --leather-dark: #1a0806;
    --gold: #d4af37;
    --gold-bright: #f5d77f;
    --gold-dim: #94772b;
    --paper: #fbf6ec;
    --paper-dark: #eee3cc;
    --ink: #221810;
    --ink-soft: #4a3b2c;
    --ink-dim: #7a6a57;
    --ruby: #7a1d1d;
    --emerald: #1c5234;
    --page-w: 470px;
    --page-h: 680px;
    --book-font-size: 15px;
    --zoom-factor: 1.0;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

  body {
    width: 100vw; height: 100vh;
    background: #050403;
    font-family: 'Crimson Pro', Georgia, serif;
    color: var(--ink);
    overflow: hidden;
    user-select: none;
  }

  /* Page-Flip Dahili Stilleri */
  .stf__parent { position: relative; display: block; box-sizing: border-box; transform-style: preserve-3d; }
  .stf__wrapper { position: relative; width: 100%; height: 100%; box-sizing: border-box; }
  .stf__block { position: absolute; width: 100%; height: 100%; box-sizing: border-box; }
  .stf__item { display: none; position: absolute; transform-style: preserve-3d; }
  .stf__item.--active { display: block; }

  #webgl-canvas {
    position: fixed; inset: 0;
    width: 100vw; height: 100vh;
    display: block; z-index: 1;
  }

  .desk-overlay-ui {
    position: fixed; top: 24px; left: 0; right: 0;
    display: flex; flex-direction: column; align-items: center;
    pointer-events: none; z-index: 10;
    opacity: 0; transform: translateY(-16px);
    transition: opacity 0.7s ease, transform 0.7s ease;
  }
  .desk-overlay-ui.visible { opacity: 1; transform: translateY(0); }
  .desk-overlay-ui.hidden { opacity: 0; transform: translateY(-16px); }
  .desk-kicker {
    font-family: 'Cinzel', serif; font-size: 11px;
    letter-spacing: 0.35em; color: var(--gold);
    text-transform: uppercase; margin-bottom: 4px;
    text-shadow: 0 2px 4px #000;
  }
  .desk-heading {
    font-family: 'Cormorant Garamond', serif;
    font-size: 32px; color: #fdf6e6; font-weight: 700;
    letter-spacing: 0.05em; text-shadow: 0 3px 8px #000;
  }
  .desk-divider {
    width: 90px; height: 1.5px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    margin: 8px auto 0;
  }
  .desk-hint {
    color: #c5ad88; font-size: 13.5px; font-style: italic; margin-top: 6px;
    text-shadow: 0 2px 4px #000;
  }

  #reader-screen {
    position: fixed; inset: 0; z-index: 20; opacity: 0; pointer-events: none;
  }
  #reader-screen.screen-active { opacity: 1; pointer-events: auto; }

  .reader-backdrop {
    position: absolute; inset: 0; z-index: 0;
    background: radial-gradient(circle at 50% 45%, rgba(13,9,6,0.78) 0%, rgba(5,4,3,0.98) 100%);
    opacity: 0; transition: opacity 0.7s ease; pointer-events: none;
  }
  #reader-screen.screen-active .reader-backdrop { opacity: 1; }

  .top-toolbar {
    position: absolute; top: 0; left: 0; right: 0; height: 54px;
    background: linear-gradient(180deg, rgba(16,11,8,0.96) 0%, rgba(24,16,12,0.88) 100%);
    border-bottom: 1px solid rgba(212,175,55,0.25);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 20px; z-index: 50; backdrop-filter: blur(8px);
    font-family: 'Cormorant Garamond', serif;
    opacity: 0; transition: opacity 0.5s ease 0.1s;
  }
  #reader-screen.screen-active .top-toolbar { opacity: 1; }

  .reader-left { display: flex; align-items: center; gap: 14px; }
  .back-to-desk-btn {
    background: rgba(212,175,55,0.18); border: 1px solid rgba(212,175,55,0.5);
    color: #f7eed7; padding: 6px 14px; border-radius: 20px;
    font-family: 'Cormorant Garamond', serif; font-size: 14px; font-weight: 600;
    cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s;
  }
  .back-to-desk-btn:hover { background: rgba(212,175,55,0.35); color: #fff; transform: translateX(-2px); }
  .reader-title { color: #f1e4c7; font-size: 17px; font-weight: 700; letter-spacing: 0.05em; }

  .search-box {
    display: flex; align-items: center; background: rgba(0,0,0,0.4);
    border: 1px solid rgba(212,175,55,0.3); border-radius: 20px; padding: 4px 12px;
  }
  .search-box input {
    background: transparent; border: none; outline: none; color: #fdf6e6;
    font-family: 'Crimson Pro', serif; font-size: 13.5px; width: 220px;
  }
  .search-box input::placeholder { color: rgba(212,175,55,0.5); font-style: italic; }

  .top-actions { display: flex; align-items: center; gap: 8px; }
  .action-btn {
    background: rgba(233,220,192,0.08); border: 1px solid rgba(212,175,55,0.35);
    color: #efe2c4; padding: 6px 12px; border-radius: 6px;
    font-family: 'Cormorant Garamond', serif; font-size: 13.5px; cursor: pointer;
  }
  .action-btn:hover { background: rgba(212,175,55,0.25); color: #fff; }

  .viewport {
    position: absolute; inset: 54px 0 60px 0;
    display: flex; align-items: center; justify-content: center;
    perspective: 2600px; overflow: hidden; z-index: 1;
  }

  .book-container {
    position: relative; width: calc(var(--page-w) * 2); height: var(--page-h);
    transform-style: preserve-3d;
    transform: translateX(0) scale(var(--zoom-factor, 1.0));
    transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .book-container.is-cover-closed { transform: translateX(calc(var(--page-w) * -0.5)) scale(var(--zoom-factor, 1.0)); }
  .book-container.is-back-closed { transform: translateX(calc(var(--page-w) * 0.5)) scale(var(--zoom-factor, 1.0)); }

  .book-shadow {
    position: absolute; left: 50%; bottom: -30px; transform: translateX(-50%);
    width: 92%; height: 46px;
    background: radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, transparent 75%);
    filter: blur(6px); pointer-events: none; z-index: 1;
  }

  #flipbook { width: calc(var(--page-w) * 2); height: var(--page-h); margin: 0 auto; }

  .page { width: 100%; height: 100%; background-color: var(--paper); overflow: hidden; }
  .page[data-density="hard"] { background-color: var(--leather-dark); }

  .cover-face {
    width: 100%; height: 100%; color: #f7eed7;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 34px 26px; text-align: center;
    border: 2px solid rgba(212,175,55,0.45); position: relative;
    box-shadow: inset 0 0 32px rgba(0,0,0,0.85);
  }
  .cover-face::before { content: ""; position: absolute; inset: 10px; border: 1.5px solid rgba(212,175,55,0.65); }

  .shamsah {
    width: 76px; height: 76px; border-radius: 50%; border: 2px solid var(--gold);
    display: flex; align-items: center; justify-content: center; margin-bottom: 14px;
    background: radial-gradient(circle, rgba(212,175,55,0.2) 0%, rgba(0,0,0,0.4) 100%);
  }
  .shamsah svg { width: 42px; height: 42px; fill: var(--gold); }

  .cover-kicker { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.35em; color: var(--gold); margin-bottom: 6px; }
  .cover-title-ar { font-family: 'Amiri', serif; font-size: 26px; font-weight: 700; color: var(--gold-bright); direction: rtl; }
  .cover-title-tr { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 22px; color: #f7eed7; margin-bottom: 6px; }
  .cover-rule { width: 60px; height: 1.5px; background: linear-gradient(90deg, transparent, var(--gold), transparent); margin: 8px auto 12px; }
  .cover-subtitle { font-family: 'Crimson Pro', serif; font-style: italic; font-size: 13.5px; color: #c9b78f; line-height: 1.4; }
  .cover-author { font-family: 'Cormorant Garamond', serif; font-size: 13px; color: var(--gold); letter-spacing: 0.15em; margin-top: 14px; }

  .page-inner {
    width: 100%; height: 100%; display: flex; flex-direction: column;
    padding: 24px 22px 18px; position: relative; font-size: var(--book-font-size);
    line-height: 1.55; color: var(--ink); user-select: text;
  }
  .page-inner::after {
    content: ""; position: absolute; inset: 10px;
    border: 1px solid rgba(212,175,55,0.45); pointer-events: none;
  }

  .running-header {
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid rgba(143,114,38,0.35); padding-bottom: 4px; margin-bottom: 8px;
    font-family: 'Cormorant Garamond', serif; font-size: 11.5px; color: var(--ink-dim);
  }
  .running-footer {
    margin-top: auto; display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid rgba(143,114,38,0.25); padding-top: 4px;
    font-family: 'Cormorant Garamond', serif; font-size: 12px; color: var(--ink-dim);
  }

  .section-kicker { font-family: 'Cinzel', serif; font-size: 9.5px; letter-spacing: 0.2em; color: var(--gold-dim); font-weight: 700; }
  .chapter-title { font-family: 'Cormorant Garamond', serif; font-size: 17.5px; font-weight: 700; color: var(--ruby); margin-bottom: 6px; border-bottom: 1px solid rgba(122,29,29,0.18); padding-bottom: 3px; }

  .ruhsat-banner {
    background: linear-gradient(135deg, rgba(28,82,52,0.08), rgba(212,175,55,0.12));
    border: 1px solid rgba(28,82,52,0.45); border-left: 4px solid var(--emerald);
    padding: 6px 9px; margin: 5px 0; border-radius: 0 4px 4px 0;
  }
  .ruhsat-badge { background: var(--emerald); color: #fff; font-family: 'Cinzel', serif; font-size: 8.5px; font-weight: 700; padding: 2px 5px; border-radius: 3px; }
  .ruhsat-text { font-weight: 600; color: var(--leather-dark); font-size: 13.5px; margin-top: 2px; }

  .mezhep-grid { display: grid; grid-template-columns: 1fr; gap: 4px; margin: 5px 0; }
  .mezhep-card { background: rgba(255,255,255,0.7); border: 1px solid rgba(143,114,38,0.25); border-radius: 3px; padding: 4px 7px; }
  .mezhep-header { display: flex; align-items: center; justify-content: space-between; }
  .mezhep-name { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 13px; }
  .mezhep-tag { font-size: 8px; padding: 1px 4px; border-radius: 3px; font-weight: 600; text-transform: uppercase; }
  .mezhep-tag.hanefi { background: rgba(28,82,52,0.15); color: #154228; border: 1px solid #1c5234; }
  .mezhep-tag.safii { background: rgba(24,62,104,0.15); color: #113155; border: 1px solid #183e68; }
  .mezhep-tag.maliki { background: rgba(122,29,29,0.15); color: #611313; border: 1px solid #7a1d1d; }
  .mezhep-tag.hanbeli { background: rgba(135,84,18,0.15); color: #633c09; border: 1px solid #875412; }

  .arabic-quote {
    font-family: 'Amiri', serif; direction: rtl; font-size: 14px;
    color: #3b2a1a; background: rgba(212,175,55,0.08); padding: 2px 6px;
    border-radius: 3px; border-right: 2px solid var(--gold); margin-top: 2px;
  }

  .telfik-box {
    background: rgba(122,29,29,0.06); border: 1px dashed rgba(122,29,29,0.4);
    padding: 5px 7px; border-radius: 3px; margin-top: 5px; font-size: 12.5px;
  }
  .telfik-title { font-weight: 700; color: var(--ruby); font-family: 'Cinzel', serif; font-size: 9px; }

  .bottom-bar {
    position: absolute; bottom: 0; left: 0; right: 0; height: 60px;
    background: linear-gradient(0deg, rgba(16,11,8,0.96) 0%, rgba(24,16,12,0.88) 100%);
    border-top: 1px solid rgba(212,175,55,0.25);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 20px; z-index: 50; backdrop-filter: blur(8px);
    font-family: 'Cormorant Garamond', serif;
    opacity: 0; transition: opacity 0.5s ease 0.1s;
  }
  #reader-screen.screen-active .bottom-bar { opacity: 1; }

  .nav-group { display: flex; align-items: center; gap: 8px; }
  .nav-btn {
    background: rgba(233,220,192,0.08); border: 1px solid rgba(212,175,55,0.35);
    color: #efe2c4; width: 34px; height: 34px; border-radius: 50%; font-size: 16px;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
  }
  .nav-btn:hover { background: rgba(212,175,55,0.25); color: #fff; }
  .page-status { color: #eeddbb; font-size: 14px; min-width: 140px; text-align: center; font-style: italic; }

  .cover-toggle-btn {
    background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(122,29,29,0.3));
    border: 1px solid var(--gold); color: #f7eed7; font-weight: 600;
    padding: 4px 11px; border-radius: 16px; cursor: pointer; font-size: 12px;
  }

  .tool-group { display: flex; align-items: center; gap: 10px; }
  .tool-subgroup {
    display: flex; align-items: center; gap: 4px; background: rgba(0,0,0,0.3);
    padding: 3px 7px; border-radius: 16px; border: 1px solid rgba(212,175,55,0.2);
  }
  .tool-label { font-size: 11.5px; color: #bfa886; }
  .tool-btn {
    background: rgba(233,220,192,0.1); border: 1px solid rgba(212,175,55,0.25);
    color: #f3e5c8; min-width: 24px; height: 24px; border-radius: 12px;
    font-size: 12px; cursor: pointer;
  }

  .modal-overlay {
    position: fixed; inset: 0; background: rgba(10,6,4,0.8); backdrop-filter: blur(5px);
    display: none; align-items: center; justify-content: center; z-index: 100;
  }
  .modal-overlay.active { display: flex; }
  .modal-card {
    background: #fbf6ec; border: 2px solid var(--gold); border-radius: 6px;
    width: 90%; max-width: 720px; max-height: 84vh; display: flex; flex-direction: column;
  }
  .modal-header {
    background: var(--leather-dark); color: var(--gold); padding: 12px 18px;
    border-bottom: 2px solid var(--gold); display: flex; align-items: center; justify-content: space-between;
  }
  .modal-close { background: none; border: none; color: #f5eed8; font-size: 20px; cursor: pointer; }
  .modal-body { padding: 14px 18px; overflow-y: auto; }
  .toc-list { list-style: none; }
  .toc-item {
    display: flex; flex-direction: column; gap: 2px; padding: 8px 4px;
    border-bottom: 1px dotted rgba(143,114,38,0.3); cursor: pointer; font-size: 13.5px;
  }
  .toc-item:hover { background: rgba(212,175,55,0.15); color: var(--ruby); }
</style>
</head>
<body>

  <div class="desk-overlay-ui" id="deskUi">
    <div class="desk-kicker">Kütüphane-i Fıkhu'l-Mukāren</div>
    <h1 class="desk-heading">Câmiu'r-Ruhas Külliyatı</h1>
    <div class="desk-divider"></div>
    <div class="desk-hint">İncelemek istediğiniz cilde dokunun (500 Mesele + 100 İcmâ + Ham Külliyat)</div>
  </div>

  <canvas id="webgl-canvas"></canvas>

  <div id="reader-screen">
    <div class="reader-backdrop"></div>

    <header class="top-toolbar">
      <div class="reader-left">
        <button class="back-to-desk-btn" id="backToDeskBtn">
          <span>‹</span> Masaya Dön
        </button>
        <div class="reader-title" id="activeBookTitle">CÂMİU'R-RUHAS</div>
      </div>

      <div class="search-box">
        <input type="text" id="searchInput" placeholder="500 Mesele veya Ham Nasslarda Ara...">
      </div>

      <div class="top-actions">
        <button class="action-btn" id="openCorpusBtn"><span>📜</span> Ham Nasslar</button>
        <button class="action-btn" id="openTocBtn"><span>☰</span> Fihrist</button>
      </div>
    </header>

    <main class="viewport">
      <div class="book-container is-cover-closed" id="bookContainer">
        <div class="book-shadow"></div>
        <div id="flipbook"></div>
      </div>
    </main>

    <footer class="bottom-bar">
      <div class="nav-group">
        <button class="cover-toggle-btn" id="closeFrontBtn">Ön Kapak</button>
        <button class="nav-btn" id="prevBtn">‹</button>
        <span class="page-status" id="pageStatus">Ön Kapak</span>
        <button class="nav-btn" id="nextBtn">›</button>
        <button class="cover-toggle-btn" id="closeBackBtn">Arka Kapak</button>
      </div>

      <div class="tool-group">
        <div class="tool-subgroup">
          <span class="tool-label">Yazı:</span>
          <button class="tool-btn" id="fontDecBtn">A−</button>
          <button class="tool-btn" id="fontIncBtn">A+</button>
        </div>
        <div class="tool-subgroup">
          <span class="tool-label">Kitap:</span>
          <button class="tool-btn" id="zoomOutBtn">−</button>
          <span class="tool-label" id="zoomDisplay" style="color:var(--gold-bright); font-weight:600; min-width:32px; text-align:center;">100%</span>
          <button class="tool-btn" id="zoomInBtn">+</button>
        </div>
      </div>
    </footer>
  </div>

  <div class="modal-overlay" id="tocModal">
    <div class="modal-card">
      <div class="modal-header">
        <h3 style="font-family:'Cinzel',serif; font-size:14px;" id="modalTitle">FİHRİST-İ MÜNDERECÂT</h3>
        <button class="modal-close" id="closeTocModal">&times;</button>
      </div>
      <div class="modal-body" id="modalTocList"></div>
    </div>
  </div>

  <!-- SIFIR HATA GÖMÜLÜ VERİ BLOĞU -->
  <script id="fikh-raw-data" type="application/json">
__DB_JSON_PLACEHOLDER__
  </script>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/page-flip@2.0.7/dist/js/page-flip.browser.min.js"></script>

  <script>
    // --- DOM ÜZERİNDEN GÜVENLİ VERİ AKTARIMI ---
    window.FIKH_DATABASE = JSON.parse(document.getElementById('fikh-raw-data').textContent);

    const BOOKS_CATALOG = [
      {
        id: "cilt-1",
        title: "CÂMİU'R-RUHAS (CİLT I)",
        sub: "İBÂDÂT KÜLLİYATI",
        color: "#38130f",
        x: -3.8,
        range: [1, 150],
        arabic: "جَامِعُ الرُّخَصِ — العِبَادَات",
        subtitle: "Tahâret, Namaz, Oruç, Zekât, Hac ve Cenâiz Düğümleri",
        author: "Mesele 001 — 150",
        theme: { leather: "#38130f", leatherDark: "#1a0806" }
      },
      {
        id: "cilt-2",
        title: "CÂMİU'R-RUHAS (CİLT II)",
        sub: "MUÂMELÂT VE AİLE",
        color: "#0d2b1a",
        x: 0,
        range: [151, 350],
        arabic: "جَامِعُ الرُّخَصِ — المُعَامَلَات",
        subtitle: "Nikâh, Talâk, Büyû', Yargı, Tıp ve Biyoetik",
        author: "Mesele 151 — 350",
        theme: { leather: "#0d2b1a", leatherDark: "#06150d" }
      },
      {
        id: "cilt-3",
        title: "CÂMİU'R-RUHAS (CİLT III)",
        sub: "ÇAĞDAŞ FIKIH & İCMÂ",
        color: "#122038",
        x: 3.8,
        range: [351, 500],
        includeIcma: true,
        arabic: "جَامِعُ الرُّخَصِ — النَّوَازِل وَالإِجْمَاع",
        subtitle: "Çağdaş Düğümler + 100 Kesin İcmâ Kanunnamesi",
        author: "Mesele 351 — 500 & İcmâ",
        theme: { leather: "#122038", leatherDark: "#09101d" }
      }
    ];

    const canvas = document.getElementById('webgl-canvas');
    const deskUi = document.getElementById('deskUi');
    const readerScreen = document.getElementById('reader-screen');
    const activeBookTitleEl = document.getElementById('activeBookTitle');

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050403);
    scene.fog = new THREE.FogExp2(0x050403, 0.038);

    const camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100);
    const CAMERA_REST = { x: 0, y: 9.8, z: 13.2 };
    const CAMERA_LOOK = { x: 0, y: 0.3, z: 0 };
    camera.position.set(0, 15.5, 21.5);

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;

    scene.add(new THREE.AmbientLight(0xd4c2a5, 0.45));
    const keyLight = new THREE.DirectionalLight(0xffeedd, 1.1);
    keyLight.position.set(4, 14, 8);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const warmFill = new THREE.PointLight(0xffaa44, 0.75, 25);
    warmFill.position.set(-5, 4, 3);
    scene.add(warmFill);

    function createWoodTexture() {
      const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 1024;
      const ctx = cv.getContext('2d'); ctx.fillStyle = '#140d08'; ctx.fillRect(0, 0, 1024, 1024);
      for (let y = 0; y < 1024; y += 4) {
        let shade = Math.sin(y * 0.02) * 12;
        ctx.fillStyle = "rgb(" + (24 + shade) + "," + (16 + shade * 0.7) + "," + (10 + shade * 0.5) + ")";
        ctx.fillRect(0, y, 1024, 4);
      }
      return new THREE.CanvasTexture(cv);
    }
    const table = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ map: createWoodTexture(), roughness: 0.55 }));
    table.rotation.x = -Math.PI / 2;
    table.receiveShadow = true;
    scene.add(table);

    function createCoverTexture(title, sub, baseColor) {
      const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 1400;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = baseColor; ctx.fillRect(0, 0, 1024, 1400);
      ctx.strokeStyle = '#d4af37'; ctx.lineWidth = 10; ctx.strokeRect(90, 90, 844, 1220);
      ctx.fillStyle = '#d4af37'; ctx.font = 'bold 52px "Cinzel", serif'; ctx.textAlign = 'center';
      ctx.fillText(title, 512, 380);
      ctx.font = 'bold 30px "Cormorant Garamond", serif'; ctx.fillText(sub, 512, 1080);
      ctx.font = '36px "Amiri", serif'; ctx.fillText('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ', 512, 700);
      return new THREE.CanvasTexture(cv);
    }

    const BOOK_W = 2.56, BOOK_H = 0.72, BOOK_D = 3.80;
    const COVER_W = BOOK_W + 0.22, COVER_H = BOOK_D + 0.22;
    const bookObjects = [];

    BOOKS_CATALOG.forEach((data) => {
      const group = new THREE.Group();
      group.position.set(data.x, 0, 0);

      const coverMap = createCoverTexture(data.title, data.sub, data.color);
      const coverMat = new THREE.MeshStandardMaterial({ map: coverMap, roughness: 0.75 });
      const plainMat = new THREE.MeshStandardMaterial({ color: data.color, roughness: 0.75 });

      const pages = new THREE.Mesh(new THREE.BoxGeometry(BOOK_W, BOOK_H, BOOK_D), new THREE.MeshStandardMaterial({ color: 0xd6be92, roughness: 0.9 }));
      pages.position.set(0.1, BOOK_H / 2 + 0.04, 0);
      group.add(pages);

      const bottomCover = new THREE.Mesh(new THREE.BoxGeometry(COVER_W, 0.08, COVER_H), plainMat);
      bottomCover.position.set(0.1, 0.04, 0);
      group.add(bottomCover);

      const topCoverHinge = new THREE.Group();
      topCoverHinge.position.set(-BOOK_W / 2 - 0.01, BOOK_H + 0.08, 0);

      const topCover = new THREE.Mesh(new THREE.BoxGeometry(COVER_W, 0.08, COVER_H), [
        plainMat, plainMat, coverMat, new THREE.MeshStandardMaterial({ color: 0xeadbb8 }), plainMat, plainMat
      ]);
      topCover.position.set(COVER_W / 2, 0, 0);
      topCoverHinge.add(topCover);
      group.add(topCoverHinge);

      group.userData = { bookData: data, topCoverHinge: topCoverHinge, coverMat: coverMat, homePosition: new THREE.Vector3(data.x, 0, 0) };
      scene.add(group);
      bookObjects.push(group);
    });

    new TWEEN.Tween(camera.position).to(CAMERA_REST, 1500).easing(TWEEN.Easing.Cubic.Out).start();
    setTimeout(() => deskUi.classList.add('visible'), 1200);

    let pageFlipInstance = null;
    let currentPagesData = [];
    const flipbookEl = document.getElementById('flipbook');
    const bookContainer = document.getElementById('bookContainer');
    const pageStatusEl = document.getElementById('pageStatus');

    function buildPagesForBook(bookData) {
      const startId = bookData.range[0];
      const endId = bookData.range[1];
      const issues = window.FIKH_DATABASE.issues.filter(i => i.id >= startId && i.id <= endId);
      const pages = [];

      pages.push({
        density: 'hard',
        html: `
          <div class="cover-face" style="background: radial-gradient(circle at 35% 25%, rgba(255,255,255,0.1), transparent 40%), linear-gradient(150deg, ${bookData.theme.leather} 0%, ${bookData.theme.leatherDark} 100%);">
            <div class="shamsah"><svg viewBox="0 0 24 24"><path d="M12,2L14.5,7.5L20.5,8.5L16,13L17.5,19L12,16L6.5,19L8,13L3.5,8.5L9.5,7.5L12,2Z"/></svg></div>
            <div class="cover-kicker">Fıkhu'l-Mukāren</div>
            <div class="cover-title-ar">${bookData.arabic}</div>
            <div class="cover-title-tr">${bookData.title}</div>
            <div class="cover-rule"></div>
            <div class="cover-subtitle">${bookData.subtitle}</div>
            <div class="cover-author">${bookData.author}</div>
          </div>
        `
      });

      pages.push({
        density: 'hard',
        html: `
          <div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#c5b592;">
            <div style="background:#fbf6ec; border:2px solid #d4af37; padding:24px; text-align:center; border-radius:4px;">
              <div style="font-family:'Cinzel',serif; font-size:13px; font-weight:700; color:#30110d;">VAKF-I KÜTÜB</div>
              <div style="font-family:'Amiri',serif; font-size:22px; color:#7a1d1d; margin:6px 0;">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>
              <p style="font-size:13px; color:#4a3b2c;">${bookData.title}<br><strong>${bookData.subtitle}</strong></p>
            </div>
          </div>
        `
      });

      let tocHtml = `
        <div class="page-inner">
          <div class="running-header"><span>${bookData.title}</span><span>MÜNDERECÂT</span></div>
          <h2 class="chapter-title">Fihrist-i Cilt</h2>
          <ul class="toc-list" style="overflow-y:auto; max-height:540px;">
      `;
      issues.slice(0, 24).forEach((it, idx) => {
        let pNum = 3 + (idx * 2);
        tocHtml += `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${pNum - 1})"><span>Mesele ${it.id}: ${it.title.substring(0, 32)}...</span><span style="color:var(--gold-dim); font-weight:700;">s. ${pNum}</span></li>`;
      });
      tocHtml += `</ul><div class="running-footer"><span>Fihrist</span><span>— 1 —</span></div></div>`;
      pages.push({ density: 'soft', html: tocHtml });

      let toc2Html = `
        <div class="page-inner">
          <div class="running-header"><span>${bookData.title}</span><span>MÜNDERECÂT II</span></div>
          <h2 class="chapter-title">Fihrist (Devam)</h2>
          <ul class="toc-list" style="overflow-y:auto; max-height:540px;">
      `;
      issues.slice(24, 48).forEach((it, idx) => {
        let pNum = 3 + ((idx + 24) * 2);
        toc2Html += `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${pNum - 1})"><span>Mesele ${it.id}: ${it.title.substring(0, 32)}...</span><span style="color:var(--gold-dim); font-weight:700;">s. ${pNum}</span></li>`;
      });
      toc2Html += `</ul><div class="running-footer"><span>Fihrist</span><span>— 2 —</span></div></div>`;
      pages.push({ density: 'soft', html: toc2Html });

      issues.forEach((it, idx) => {
        let pNum = 3 + (idx * 2);
        pages.push({
          density: 'soft',
          html: `
            <div class="page-inner">
              <div class="running-header"><span>${it.chapter}</span><span>MESELE ${it.id}</span></div>
              <div class="section-kicker">${it.chapter}</div>
              <h2 class="chapter-title">Mesele ${it.id}: ${it.title}</h2>
              <div class="ruhsat-banner">
                <span class="ruhsat-badge">RUHSAT &amp; LİTE TATBİKAT</span>
                <div class="ruhsat-text">${it.ruhsat.hukum}</div>
                <div style="font-size:11px; color:var(--emerald); margin-top:2px; font-weight:600;">Esas Alınan: ${it.ruhsat.mezhep}</div>
              </div>
              <div class="mezhep-grid">
                <div class="mezhep-card">
                  <div class="mezhep-header"><span class="mezhep-name">Hanefî</span><span class="mezhep-tag hanefi">Hanefî</span></div>
                  <div style="font-size:12px;">${it.madhabs.hanefi.hukum}</div>
                  ${it.madhabs.hanefi.kaynak ? `<div class="arabic-quote">${it.madhabs.hanefi.kaynak.substring(0, 100)}...</div>` : ''}
                </div>
                <div class="mezhep-card">
                  <div class="mezhep-header"><span class="mezhep-name">Şâfiî</span><span class="mezhep-tag safii">Şâfiî</span></div>
                  <div style="font-size:12px;">${it.madhabs.safii.hukum}</div>
                </div>
                <div class="mezhep-card">
                  <div class="mezhep-header"><span class="mezhep-name">Mâlikî</span><span class="mezhep-tag maliki">Mâlikî</span></div>
                  <div style="font-size:12px;">${it.madhabs.maliki.hukum}</div>
                </div>
                <div class="mezhep-card">
                  <div class="mezhep-header"><span class="mezhep-name">Hanbelî</span><span class="mezhep-tag hanbeli">Hanbelî</span></div>
                  <div style="font-size:12px;">${it.madhabs.hanbeli.hukum}</div>
                </div>
              </div>
              <div class="running-footer"><span>Câmiu'r-Ruhas</span><span>— ${pNum} —</span></div>
            </div>
          `
        });

        pages.push({
          density: 'soft',
          html: `
            <div class="page-inner">
              <div class="running-header"><span>MESELE ${it.id}</span><span>TAHKÎK &amp; TELFÎK</span></div>
              <div class="section-kicker">USÛL VE İLLET</div>
              <h3 style="font-family:'Cormorant Garamond',serif; margin:4px 0; font-size:16.5px; color:var(--leather-outer);">Menşe-i Hilâf ve Hikmet</h3>
              <div style="font-size:13px; text-align:justify; line-height:1.5; margin-bottom:8px;">${it.hilaf || 'Dört mezhebin delalet ve usûl kurallarına göre tahrîc edilmiştir.'}</div>
              <div class="telfik-box">
                <div class="telfik-title">⚖ TELFÎK DENETİMİ VE FETVÂ GÜVENCESİ</div>
                <div style="line-height:1.45; margin-top:2px;">${it.telfik || it.ruhsat.guvence || 'İcmâ-i mürekkep riski bulunmamaktadır.'}</div>
              </div>
              <div class="running-footer"><span>Tahkîk</span><span>— ${pNum + 1} —</span></div>
            </div>
          `
        });
      });

      if (bookData.includeIcma && window.FIKH_DATABASE.icma.length > 0) {
        pages.push({
          density: 'hard',
          html: `
            <div class="cover-face" style="background:#111c2e;">
              <div class="shamsah"><svg viewBox="0 0 24 24"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,22A10,10 0 0,0 12,2Z"/></svg></div>
              <div class="cover-title-ar">الإِجْمَاعُ وَالمُتَّفَقُ عَلَيْهِ</div>
              <h2 style="font-family:'Cinzel',serif; font-size:18px; color:#f7eed7; margin-top:10px;">DÖRT MEZHEBİN İTTİFAK KANUNNAMESİ</h2>
              <div class="cover-rule"></div>
              <p style="font-size:13px; color:#c9b78f;">Alternatifsiz ve Kesin 100 İcmâ Hükmü</p>
            </div>
          `
        });

        for (let i = 0; i < window.FIKH_DATABASE.icma.length; i += 6) {
          const chunk = window.FIKH_DATABASE.icma.slice(i, i + 6);
          let icmaHtml = `<div class="page-inner"><div class="running-header"><span>EL-MÜTTEFEK ALEYH</span><span>İCMÂ HÜKÜMLERİ</span></div><h2 class="chapter-title">Dört Mezhebin İttifakı (${i + 1} - ${Math.min(i + 6, window.FIKH_DATABASE.icma.length)})</h2><div style="display:flex; flex-direction:column; gap:6px;">`;
          chunk.forEach(ic => {
            icmaHtml += `<div style="background:rgba(255,255,255,0.6); border-left:3px solid var(--gold); padding:5px 8px; font-size:12.5px;"><strong>${ic.id}. ${ic.title}:</strong> ${ic.rule}</div>`;
          });
          icmaHtml += `</div><div class="running-footer"><span>İcmâ Kanunu</span><span>— İcmâ —</span></div></div>`;
          pages.push({ density: 'soft', html: icmaHtml });
        }
      }

      pages.push({
        density: 'hard',
        html: `
          <div class="cover-face" style="justify-content:center; background: radial-gradient(circle at 35% 25%, rgba(255,255,255,0.1), transparent 40%), linear-gradient(150deg, ${bookData.theme.leather} 0%, ${bookData.theme.leatherDark} 100%);">
            <div class="shamsah"><svg viewBox="0 0 24 24"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/></svg></div>
            <div class="cover-title-ar" style="font-size:22px;">تَمَّتْ بِحَمْدِ اللَّهِ</div>
            <div class="cover-rule"></div>
            <p style="font-family:'Cormorant Garamond',serif; font-size:15px; color:#c9b78f;">${bookData.title}</p>
          </div>
        `
      });

      return pages;
    }

    function updateReaderUi(pageIdx) {
      const total = currentPagesData.length;
      bookContainer.classList.remove('is-cover-closed', 'is-back-closed');
      if (pageIdx === 0) {
        bookContainer.classList.add('is-cover-closed');
        pageStatusEl.innerHTML = '<strong>Ön Kapak</strong>';
      } else if (pageIdx === total - 1) {
        bookContainer.classList.add('is-back-closed');
        pageStatusEl.innerHTML = '<strong>Arka Kapak</strong>';
      } else {
        pageStatusEl.textContent = 'Sayfa ' + pageIdx + ' – ' + Math.min(pageIdx + 1, total - 1) + ' / ' + (total - 2);
      }
    }

    function prepareReader(bookData) {
      activeBookTitleEl.textContent = bookData.title;
      if (pageFlipInstance) { pageFlipInstance.destroy(); pageFlipInstance = null; }
      flipbookEl.innerHTML = '';

      currentPagesData = buildPagesForBook(bookData);
      currentPagesData.forEach(p => {
        const div = document.createElement('div');
        div.className = 'page';
        div.setAttribute('data-density', p.density);
        div.innerHTML = p.html;
        flipbookEl.appendChild(div);
      });

      const isMobile = window.innerWidth <= 920;
      const targetW = isMobile ? Math.round(window.innerWidth * 0.92) : 470;
      const targetH = isMobile ? Math.round(window.innerHeight * 0.68) : 680;

      pageFlipInstance = new St.PageFlip(flipbookEl, {
        width: targetW, height: targetH, size: 'stretch',
        minWidth: 280, maxWidth: 1200, minHeight: 380, maxHeight: 1400,
        showCover: true, drawShadow: true, flippingTime: 700, startPage: 0
      });

      pageFlipInstance.loadFromHTML(document.querySelectorAll('#flipbook .page'));
      pageFlipInstance.on('flip', e => updateReaderUi(e.data));
      updateReaderUi(0);

      const r = flipbookEl.getBoundingClientRect();
      return { left: r.left, top: r.top, width: targetW, height: targetH };
    }

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let selectedBookGroup = null;
    let isTransitioning = false;

    function pickBook(clientX, clientY) {
      mouse.x = (clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(clientY / window.innerHeight) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(bookObjects, true);
      if (!hits.length) return null;
      let o = hits[0].object;
      while (o.parent && !o.userData.topCoverHinge) o = o.parent;
      return o.userData.topCoverHinge ? o : null;
    }

    window.addEventListener('pointerdown', e => {
      if (isTransitioning || selectedBookGroup) return;
      const hit = pickBook(e.clientX, e.clientY);
      if (hit) triggerOpenBook(hit);
    });

    function triggerOpenBook(group) {
      isTransitioning = true;
      selectedBookGroup = group;
      deskUi.classList.add('hidden');
      const data = group.userData.bookData;

      prepareReader(data);

      new TWEEN.Tween(group.position).to({ x: 0, y: 5.5, z: 6.5 }, 800).easing(TWEEN.Easing.Cubic.InOut).start();
      new TWEEN.Tween(group.rotation).to({ x: 0.95, y: 0, z: 0 }, 800).easing(TWEEN.Easing.Cubic.InOut)
        .onComplete(() => {
          group.visible = false;
          readerScreen.classList.add('screen-active');
          isTransitioning = false;
          setTimeout(() => pageFlipInstance && pageFlipInstance.flipNext('bottom'), 350);
        }).start();
    }

    function triggerCloseBook() {
      if (!selectedBookGroup || isTransitioning) return;
      isTransitioning = true;
      const group = selectedBookGroup;
      if (pageFlipInstance) pageFlipInstance.turnToPage(0);

      setTimeout(() => {
        group.visible = true;
        readerScreen.classList.remove('screen-active');
        new TWEEN.Tween(group.position).to(group.userData.homePosition, 800).easing(TWEEN.Easing.Cubic.InOut).start();
        new TWEEN.Tween(group.rotation).to({ x: 0, y: 0, z: 0 }, 800).easing(TWEEN.Easing.Cubic.InOut)
          .onComplete(() => {
            selectedBookGroup = null;
            isTransitioning = false;
            deskUi.classList.remove('hidden');
          }).start();
      }, 600);
    }

    document.getElementById('backToDeskBtn').addEventListener('click', triggerCloseBook);
    document.getElementById('prevBtn').addEventListener('click', () => pageFlipInstance && pageFlipInstance.flipPrev('bottom'));
    document.getElementById('nextBtn').addEventListener('click', () => pageFlipInstance && pageFlipInstance.flipNext('bottom'));
    document.getElementById('closeFrontBtn').addEventListener('click', () => pageFlipInstance && pageFlipInstance.turnToPage(0));
    document.getElementById('closeBackBtn').addEventListener('click', () => pageFlipInstance && pageFlipInstance.turnToPage(currentPagesData.length - 1));

    let currentZoom = 1.0;
    document.getElementById('zoomInBtn').addEventListener('click', () => {
      currentZoom = Math.min(1.5, currentZoom + 0.1);
      document.documentElement.style.setProperty('--zoom-factor', currentZoom);
      document.getElementById('zoomDisplay').textContent = Math.round(currentZoom * 100) + '%';
    });
    document.getElementById('zoomOutBtn').addEventListener('click', () => {
      currentZoom = Math.max(0.7, currentZoom - 0.1);
      document.documentElement.style.setProperty('--zoom-factor', currentZoom);
      document.getElementById('zoomDisplay').textContent = Math.round(currentZoom * 100) + '%';
    });

    let currentFontSize = 15;
    document.getElementById('fontIncBtn').addEventListener('click', () => {
      currentFontSize = Math.min(19, currentFontSize + 1);
      document.documentElement.style.setProperty('--book-font-size', currentFontSize + 'px');
    });
    document.getElementById('fontDecBtn').addEventListener('click', () => {
      currentFontSize = Math.max(12, currentFontSize - 1);
      document.documentElement.style.setProperty('--book-font-size', currentFontSize + 'px');
    });

    const searchInput = document.getElementById('searchInput');
    const tocModal = document.getElementById('tocModal');
    const modalTocList = document.getElementById('modalTocList');

    searchInput.addEventListener('input', e => {
      const q = e.target.value.toLowerCase().trim();
      if (q.length < 2) return;
      
      const issueResults = window.FIKH_DATABASE.issues.filter(it => 
        it.title.toLowerCase().includes(q) || 
        it.ruhsat.hukum.toLowerCase().includes(q) ||
        it.chapter.toLowerCase().includes(q)
      );

      const rawResults = (window.FIKH_DATABASE.raw_corpus || []).filter(n =>
        n.metin.toLowerCase().includes(q) ||
        (n.bab && n.bab.toLowerCase().includes(q)) ||
        (n.eser && n.eser.toLowerCase().includes(q))
      );

      let resHtml = '<div style="padding-bottom:6px; font-weight:700; color:var(--ruby);">' + issueResults.length + ' Mesele | ' + rawResults.length + ' Aslî Nass Bulundu:</div><ul class="toc-list">';
      
      issueResults.slice(0, 20).forEach(r => {
        resHtml += '<li class="toc-item" onclick="openFoundIssue(' + r.id + ')"><span><strong>[Mesele ' + r.id + ']</strong> ' + r.title + '</span><span style="color:var(--emerald); font-size:12px;">' + r.ruhsat.mezhep + '</span></li>';
      });

      if (rawResults.length > 0) {
        resHtml += '<li style="padding:10px 0 4px; font-weight:700; color:var(--gold-dim); border-bottom:2px solid var(--gold);">KLASİK KORPUS HAM NASSLARI:</li>';
        rawResults.slice(0, 15).forEach(n => {
          resHtml += '<li class="toc-item" style="background:rgba(212,175,55,0.06); margin-top:4px;"><span><strong>[' + n.mezhep + ' - ' + n.muellif + ' (' + n.eser + ')]</strong> ' + (n.bab || n.kitab) + '</span><div class="arabic-quote" style="font-size:13px;">' + n.metin + '</div></li>';
        });
      }

      resHtml += '</ul>';
      modalTocList.innerHTML = resHtml;
      document.getElementById('modalTitle').textContent = "EVRENSEL ARAMA SONUÇLARI";
      tocModal.classList.add('active');
    });

    window.openFoundIssue = function(issueId) {
      tocModal.classList.remove('active');
      let targetBook = BOOKS_CATALOG.find(b => issueId >= b.range[0] && issueId <= b.range[1]);
      if (!targetBook) return;

      if (!selectedBookGroup || selectedBookGroup.userData.bookData.id !== targetBook.id) {
        let targetGroup = bookObjects.find(g => g.userData.bookData.id === targetBook.id);
        if (targetGroup) triggerOpenBook(targetGroup);
      }

      setTimeout(() => {
        let offset = issueId - targetBook.range[0];
        let targetPage = 4 + (offset * 2);
        if (pageFlipInstance) pageFlipInstance.turnToPage(targetPage);
      }, 900);
    };

    document.getElementById('openCorpusBtn').addEventListener('click', () => {
      const rawList = window.FIKH_DATABASE.raw_corpus || [];
      let html = '<div style="padding-bottom:8px; font-weight:700; color:var(--ruby);">KORPUSTAN DERLENEN ASLÎ ARAPÇA NASSLAR (' + rawList.length + ' Düğüm):</div><ul class="toc-list">';
      rawList.slice(0, 40).forEach(n => {
        html += '<li class="toc-item" style="background:rgba(212,175,55,0.05); margin-bottom:6px; border-left:3px solid var(--gold); padding:6px 10px;"><span><strong>[' + n.mezhep + '] ' + n.muellif + ' — ' + n.eser + ' (C:' + n.cilt + ', S:' + n.sayfa + ')</strong></span><div style="font-size:12px; color:var(--ink-soft);">' + (n.kitab || '') + ' - ' + (n.bab || '') + '</div><div class="arabic-quote" style="font-size:13.5px; margin-top:4px;">' + n.metin + '</div></li>';
      });
      html += '</ul>';
      modalTocList.innerHTML = html;
      document.getElementById('modalTitle').textContent = "HAM NASSLAR VE KLASİK FIKIH METİNLERİ";
      tocModal.classList.add('active');
    });

    document.getElementById('openTocBtn').addEventListener('click', () => {
      if (!selectedBookGroup) return;
      const bData = selectedBookGroup.userData.bookData;
      const issues = window.FIKH_DATABASE.issues.filter(i => i.id >= bData.range[0] && i.id <= bData.range[1]);
      let html = '<ul class="toc-list">';
      issues.forEach((it, idx) => {
        let pNum = 4 + (idx * 2);
        html += `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${pNum}); tocModal.classList.remove('active');"><span><strong>Mesele ${it.id}:</strong> ${it.title}</span><span style="color:var(--gold-dim); font-weight:700;">s. ${pNum}</span></li>`;
      });
      html += '</ul>';
      modalTocList.innerHTML = html;
      document.getElementById('modalTitle').textContent = bData.title + " FİHRİSTİ";
      tocModal.classList.add('active');
    });

    document.getElementById('closeTocModal').addEventListener('click', () => tocModal.classList.remove('active'));

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    function animate(time) {
      requestAnimationFrame(animate);
      TWEEN.update(time);
      camera.lookAt(CAMERA_LOOK.x, CAMERA_LOOK.y, CAMERA_LOOK.z);
      renderer.render(scene, camera);
    }
    animate();
  </script>
</body>
</html>'''

    full_output = HTML_TEMPLATE.replace("__DB_JSON_PLACEHOLDER__", db_json_safe)

    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(full_output)

    size_mb = os.path.getsize(OUTPUT_HTML_PATH) / (1024 * 1024)
    print("=" * 80)
    print(f"[✓] HATASIZ STANDALONE KÜLLİYAT ÜRETİLDİ: {OUTPUT_HTML_PATH}")
    print(f"    Dosya Boyutu: {size_mb:.2f} MB")
    print("=" * 80)

if __name__ == "__main__":
    build_clean_html()
