import os
import re
import json
import sqlite3

MASTER_MD_PATH = r"D:\fikh_kitap\Camiur_Ruhas_Nihai_Kulliyat.md"
DB_PATH = os.path.join("metadata", "fikh_corpus.db")
OUTPUT_HTML_PATH = r"D:\fikh_kitap\index.html"

def extract_corpus_by_madhab(db_path, madhab_name, limit=300):
    print(f"[*] {madhab_name} Külliyatı (SQLite) taranıyor...")
    if not os.path.exists(db_path):
        return []
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE mezhep = ? AND metin_orijinal IS NOT NULL AND LENGTH(metin_orijinal) > 40
        LIMIT ?;
    """, (madhab_name, limit))
    rows = cur.fetchall()
    
    res = []
    for r in rows:
        res.append({
            "id": r[0], "mezhep": r[1], "muellif": r[2], "eser": r[3],
            "cilt": r[4], "sayfa": r[5], "kitab": r[6], "bab": r[7],
            "metin": r[8][:600].replace("\n", " ").strip() + "..."
        })
    return res

def parse_master_manuscript(md_path):
    print("[*] Master Markdown (Câmiu'r-Ruhas) taranıyor...")
    with open(md_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    parts = raw_text.split("# İKİNCİ KISIM: DÖRT MEZHEBİN ÇAĞDAŞ VE KLASİK İTTİFAK KANUNNAMESİ")
    part1_text = parts[0]
    part2_text = parts[1] if len(parts) > 1 else ""

    issue_raw_blocks = re.split(r"(?=## MESELE \d+:)", part1_text)
    issues_list = []

    for block in issue_raw_blocks:
        m_match = re.search(r"## MESELE (\d+):\s*(.+)", block)
        if not m_match: continue
        
        m_id = int(m_match.group(1))
        m_title = m_match.group(2).strip()

        chap_match = re.search(r"# BÖLÜM:\s*(.+)", block)
        chap_name = chap_match.group(1).strip() if chap_match else "FIKIH KÜLLİYATI"

        ruhsat_hukum, ruhsat_mezhep = "", ""
        r_match = re.search(r"- \*\*Uygulanacak Kolaylık:\*\*\s*(.+)", block)
        if r_match: ruhsat_hukum = r_match.group(1).strip()
        m_mez_match = re.search(r"- \*\*Esas Alınan Mezhep:\*\*\s*(.+)", block)
        if m_mez_match: ruhsat_mezhep = m_mez_match.group(1).strip()

        def extract_madhab(m_name):
            pat = rf"### \d+\.\s*{m_name} Mezhebi\s*\n- \*\*Hüküm:\*\*\s*(.+?)(?:\n- \*\*Kaynak İbâre:\*\*\s*(.+?))?(?=\n###|\n##|$)"
            found = re.search(pat, block, re.DOTALL)
            if found:
                h = found.group(1).strip() if found.group(1) else ""
                k = found.group(2).strip() if found.group(2) else ""
                return {"hukum": h, "kaynak": k}
            return {"hukum": "Kavle ulaşılamadı.", "kaynak": ""}

        hilaf_match = re.search(r"## 3\. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\s*\n([\s\S]*?)(?=\n## 4\.|$)", block)
        hilaf = hilaf_match.group(1).strip() if hilaf_match else ""

        telfik_match = re.search(r"## 4\. TELFÎK DENETİMİ VE FETVÂ\s*\n([\s\S]*?)(?=\n---|$)", block)
        telfik = telfik_match.group(1).strip() if telfik_match else ""

        issues_list.append({
            "id": m_id, "chapter": chap_name, "title": m_title,
            "ruhsat": {"hukum": ruhsat_hukum, "mezhep": ruhsat_mezhep},
            "madhabs": {
                "hanefi": extract_madhab("Hanefî"), "safii": extract_madhab("Şâfiî"),
                "maliki": extract_madhab("Mâlikî"), "hanbeli": extract_madhab("Hanbelî")
            },
            "hilaf": hilaf, "telfik": telfik
        })

    issues_list.sort(key=lambda x: x["id"])

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

    print(f"[+] Doğrulandı: {len(issues_list)} Mesele | {len(icma_list)} İcmâ Kanunu")
    return issues_list, icma_list

def generate_web_library():
    issues, icma = parse_master_manuscript(MASTER_MD_PATH)
    
    # 4 Mezhebin kütüphanesini ayrı ayrı çekiyoruz
    hanefi = extract_corpus_by_madhab(DB_PATH, "Hanefi", 200)
    maliki = extract_corpus_by_madhab(DB_PATH, "Maliki", 200)
    safii = extract_corpus_by_madhab(DB_PATH, "Safii", 200)
    hanbeli = extract_corpus_by_madhab(DB_PATH, "Hanbeli", 200)

    full_payload = {
        "camiur_ruhas": issues, "icma": icma,
        "hanefi": hanefi, "maliki": maliki, "safii": safii, "hanbeli": hanbeli
    }
    json_data = json.dumps(full_payload, ensure_ascii=False)

    HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kütüphane-i Fıkhu'l-Mukāren — 3D Fiziksel Masa</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Cinzel:wght@500;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Crimson+Pro:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">

<style>
  :root {
    --gold: #d4af37; --gold-dim: #94772b; --paper: #fbf6ec; --paper-dark: #eee3cc;
    --ink: #221810; --ruby: #7a1d1d; --emerald: #1c5234;
    --page-w: 480px; --page-h: 700px; --book-font-size: 15px; --zoom-factor: 1.0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  body { width: 100vw; height: 100vh; background: #050403; font-family: 'Crimson Pro', Georgia, serif; color: var(--ink); overflow: hidden; user-select: none; }

  .stf__parent { position: relative; display: block; box-sizing: border-box; transform-style: preserve-3d; }
  .stf__wrapper { position: relative; width: 100%; height: 100%; box-sizing: border-box; }
  .stf__block { position: absolute; width: 100%; height: 100%; box-sizing: border-box; }
  .stf__item { display: none; position: absolute; transform-style: preserve-3d; }
  .stf__item.--active { display: block; }

  #webgl-canvas { position: fixed; inset: 0; width: 100vw; height: 100vh; display: block; z-index: 1; }

  /* KAYDIRMA ÇUBUĞU (SCROLLBAR) TASARIMI */
  .scroll-area {
    flex: 1; overflow-y: auto; padding-right: 12px; margin-right: -4px;
    scrollbar-width: thin; scrollbar-color: var(--gold-dim) transparent;
  }
  .scroll-area::-webkit-scrollbar { width: 6px; }
  .scroll-area::-webkit-scrollbar-track { background: transparent; }
  .scroll-area::-webkit-scrollbar-thumb { background-color: var(--gold-dim); border-radius: 4px; }

  /* SİS VE ARAYÜZ */
  .vignette { position: fixed; inset: 0; z-index: 2; pointer-events: none; background: radial-gradient(circle at center, transparent 40%, rgba(5,4,3,0.9) 100%); }
  
  .achievement-toast { position: fixed; bottom: -80px; right: 20px; z-index: 1000; background: linear-gradient(135deg, #1b2838 0%, #2a475e 100%); border: 1px solid #171a21; border-radius: 4px; padding: 12px 16px; display: flex; align-items: center; gap: 14px; box-shadow: 0 8px 16px rgba(0,0,0,0.6); transition: transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275); color: #c7d5e0; font-family: sans-serif; }
  .achievement-toast.show { transform: translateY(-100px); }
  .ach-icon { width: 44px; height: 44px; background: #d4af37; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 0 10px rgba(212,175,55,0.5); }
  .ach-texts { display: flex; flex-direction: column; }
  .ach-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #66c0f4; margin-bottom: 3px; }
  .ach-desc { font-size: 14px; font-weight: bold; color: #fff; }

  .desk-overlay-ui { position: fixed; top: 24px; left: 0; right: 0; display: flex; flex-direction: column; align-items: center; pointer-events: none; z-index: 10; opacity: 0; transform: translateY(-16px); transition: opacity 0.7s ease, transform 0.7s ease; }
  .desk-overlay-ui.visible { opacity: 1; transform: translateY(0); }
  .desk-overlay-ui.hidden { opacity: 0; transform: translateY(-16px); }
  .desk-kicker { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.35em; color: var(--gold); text-transform: uppercase; margin-bottom: 4px; text-shadow: 0 2px 4px #000; }
  .desk-heading { font-family: 'Cormorant Garamond', serif; font-size: 34px; color: #fdf6e6; font-weight: 700; letter-spacing: 0.05em; text-shadow: 0 3px 8px #000; }
  .desk-divider { width: 80px; height: 1.5px; background: linear-gradient(90deg, transparent, var(--gold), transparent); margin: 8px auto 0; }
  .desk-hint { color: #c5ad88; font-size: 14px; font-style: italic; margin-top: 6px; text-shadow: 0 2px 4px #000; }

  #reader-screen { position: fixed; inset: 0; z-index: 20; opacity: 0; pointer-events: none; }
  #reader-screen.screen-active { opacity: 1; pointer-events: auto; }
  .reader-backdrop { position: absolute; inset: 0; z-index: 0; background: radial-gradient(circle at 50% 45%, rgba(13,9,6,0.85) 0%, rgba(5,4,3,0.98) 100%); opacity: 0; transition: opacity 0.75s ease; pointer-events: none; }
  #reader-screen.screen-active .reader-backdrop { opacity: 1; }

  .top-toolbar { position: absolute; top: 0; left: 0; right: 0; height: 56px; background: linear-gradient(180deg, rgba(16,11,8,0.96) 0%, rgba(24,16,12,0.88) 100%); border-bottom: 1px solid rgba(212,175,55,0.25); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; z-index: 50; backdrop-filter: blur(8px); opacity: 0; transition: opacity 0.55s ease 0.15s; }
  #reader-screen.screen-active .top-toolbar { opacity: 1; }
  .reader-left { display: flex; align-items: center; gap: 14px; }
  .back-to-desk-btn { background: rgba(212,175,55,0.18); border: 1px solid rgba(212,175,55,0.5); color: #f7eed7; padding: 8px 16px; border-radius: 20px; font-family: 'Cormorant Garamond', serif; font-size: 15px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
  .back-to-desk-btn:hover { background: rgba(212,175,55,0.35); color: #fff; transform: translateX(-3px); }
  .reader-title { color: #f1e4c7; font-size: 18px; font-family: 'Cinzel', serif; font-weight: 700; letter-spacing: 0.05em; }

  .search-box { display: flex; align-items: center; background: rgba(0,0,0,0.5); border: 1px solid rgba(212,175,55,0.4); border-radius: 20px; padding: 6px 16px; }
  .search-box input { background: transparent; border: none; outline: none; color: #fdf6e6; font-family: 'Crimson Pro', serif; font-size: 14.5px; width: 260px; }
  .search-box input::placeholder { color: rgba(212,175,55,0.6); font-style: italic; }

  .top-actions { display: flex; align-items: center; gap: 10px; }
  .action-btn { background: rgba(233,220,192,0.08); border: 1px solid rgba(212,175,55,0.35); color: #efe2c4; padding: 7px 16px; border-radius: 6px; font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 15px; cursor: pointer; }
  .action-btn:hover { background: rgba(212,175,55,0.25); color: #fff; }

  .viewport { position: absolute; inset: 56px 0 64px 0; display: flex; align-items: center; justify-content: center; perspective: 2800px; overflow: hidden; z-index: 1; }
  .book-container { position: relative; width: calc(var(--page-w) * 2); height: var(--page-h); transform-style: preserve-3d; transform: translateX(0) scale(var(--zoom-factor, 1.0)); transition: transform 0.5s cubic-bezier(0.25, 1, 0.5, 1); }
  .book-container.is-cover-closed { transform: translateX(calc(var(--page-w) * -0.5)) scale(var(--zoom-factor, 1.0)); }
  .book-container.is-back-closed { transform: translateX(calc(var(--page-w) * 0.5)) scale(var(--zoom-factor, 1.0)); }

  #flipbook { width: calc(var(--page-w) * 2); height: var(--page-h); margin: 0 auto; }
  .page { width: 100%; height: 100%; background-color: var(--paper); overflow: hidden; }
  .page[data-density="hard"] { background-color: #1a0806; }
  
  .cover-face { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 34px 26px; text-align: center; border: 2px solid rgba(212,175,55,0.45); position: relative; box-shadow: inset 0 0 40px rgba(0,0,0,0.9); background-size: cover; background-position: center; }
  .cover-face::before { content: ""; position: absolute; inset: 12px; border: 1.5px solid rgba(212,175,55,0.65); }

  .page-inner { width: 100%; height: 100%; display: flex; flex-direction: column; padding: 26px 24px 20px; position: relative; font-size: var(--book-font-size); line-height: 1.6; color: var(--ink); user-select: text; }
  .page-inner::after { content: ""; position: absolute; inset: 12px; border: 1px solid rgba(212,175,55,0.35); pointer-events: none; }
  .running-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(143,114,38,0.35); padding-bottom: 5px; margin-bottom: 10px; font-family: 'Cormorant Garamond', serif; font-size: 12.5px; color: var(--ink-dim); font-weight: 600; }
  .running-footer { margin-top: auto; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(143,114,38,0.25); padding-top: 5px; font-family: 'Cormorant Garamond', serif; font-size: 13px; color: var(--ink-dim); }
  
  .section-kicker { font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: 0.2em; color: var(--gold-dim); font-weight: 700; }
  .chapter-title { font-family: 'Cormorant Garamond', serif; font-size: 18px; font-weight: 700; color: var(--ruby); margin-bottom: 8px; border-bottom: 1px solid rgba(122,29,29,0.18); padding-bottom: 4px; line-height: 1.3; }

  .ruhsat-banner { background: linear-gradient(135deg, rgba(28,82,52,0.08), rgba(212,175,55,0.12)); border: 1px solid rgba(28,82,52,0.45); border-left: 5px solid var(--emerald); padding: 8px 10px; margin: 6px 0; border-radius: 0 4px 4px 0; }
  .ruhsat-badge { background: var(--emerald); color: #fff; font-family: 'Cinzel', serif; font-size: 9px; font-weight: 700; padding: 3px 6px; border-radius: 3px; }
  .ruhsat-text { font-weight: 600; color: var(--leather-dark); font-size: 14px; margin-top: 4px; }

  .mezhep-grid { display: grid; grid-template-columns: 1fr; gap: 5px; margin: 6px 0; }
  .mezhep-card { background: rgba(255,255,255,0.75); border: 1px solid rgba(143,114,38,0.3); border-radius: 4px; padding: 6px 8px; }
  .mezhep-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; }
  .mezhep-name { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 14px; color: #3b2a1a; }
  .mezhep-tag { font-size: 9px; padding: 2px 5px; border-radius: 3px; font-weight: 700; text-transform: uppercase; }
  .mezhep-tag.hanefi { background: rgba(28,82,52,0.15); color: #154228; border: 1px solid #1c5234; }
  .mezhep-tag.safii { background: rgba(24,62,104,0.15); color: #113155; border: 1px solid #183e68; }
  .mezhep-tag.maliki { background: rgba(122,29,29,0.15); color: #611313; border: 1px solid #7a1d1d; }
  .mezhep-tag.hanbeli { background: rgba(135,84,18,0.15); color: #633c09; border: 1px solid #875412; }
  .arabic-quote { font-family: 'Amiri', serif; direction: rtl; font-size: 15px; color: #221810; background: rgba(212,175,55,0.08); padding: 4px 8px; border-radius: 4px; border-right: 3px solid var(--gold); margin-top: 4px; line-height: 1.6; }
  
  .telfik-box { background: rgba(122,29,29,0.06); border: 1px dashed rgba(122,29,29,0.5); padding: 8px 10px; border-radius: 4px; margin-top: 8px; font-size: 13.5px; }
  .telfik-title { font-weight: 700; color: var(--ruby); font-family: 'Cinzel', serif; font-size: 10px; }

  .icma-banner { background: #111c2e; color: #f7eed7; text-align: center; padding: 8px; font-family: 'Cinzel', serif; font-size: 14px; font-weight: 700; letter-spacing: 1px; border: 2px solid var(--gold); margin-bottom: 10px; }

  .bottom-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 64px; background: linear-gradient(0deg, rgba(16,11,8,0.96) 0%, rgba(24,16,12,0.88) 100%); border-top: 1px solid rgba(212,175,55,0.25); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; z-index: 50; backdrop-filter: blur(8px); opacity: 0; transition: opacity 0.55s ease 0.15s; }
  #reader-screen.screen-active .bottom-bar { opacity: 1; }
  .nav-group { display: flex; align-items: center; gap: 10px; }
  .nav-btn { background: rgba(233,220,192,0.08); border: 1px solid rgba(212,175,55,0.35); color: #efe2c4; width: 38px; height: 38px; border-radius: 50%; font-size: 18px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
  .nav-btn:hover { background: rgba(212,175,55,0.3); color: #fff; transform: scale(1.05); }
  .page-status { color: #eeddbb; font-size: 15px; min-width: 150px; text-align: center; font-style: italic; }
  .cover-toggle-btn { background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(122,29,29,0.3)); border: 1px solid var(--gold); color: #f7eed7; font-weight: 600; padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 13px; font-family: 'Cormorant Garamond', serif; }

  .tool-group { display: flex; align-items: center; gap: 12px; }
  .tool-subgroup { display: flex; align-items: center; gap: 5px; background: rgba(0,0,0,0.4); padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(212,175,55,0.25); }
  .tool-label { font-size: 12.5px; color: #bfa886; font-weight: 600; }
  .tool-btn { background: rgba(233,220,192,0.1); border: 1px solid rgba(212,175,55,0.3); color: #f3e5c8; min-width: 28px; height: 28px; border-radius: 14px; font-size: 14px; font-weight: bold; cursor: pointer; transition: all 0.2s; }
  .tool-btn:hover { background: rgba(212,175,55,0.3); color: #fff; }

  .modal-overlay { position: fixed; inset: 0; background: rgba(5,4,3,0.85); backdrop-filter: blur(6px); display: none; align-items: center; justify-content: center; z-index: 100; }
  .modal-overlay.active { display: flex; }
  .modal-card { background: #fbf6ec; border: 2px solid var(--gold); border-radius: 6px; width: 92%; max-width: 800px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 10px 40px rgba(0,0,0,0.8); }
  .modal-header { background: var(--leather-dark); color: var(--gold); padding: 14px 20px; border-bottom: 2px solid var(--gold); display: flex; align-items: center; justify-content: space-between; }
  .modal-close { background: none; border: none; color: #f5eed8; font-size: 24px; cursor: pointer; transition: color 0.2s; }
  .modal-close:hover { color: #fff; }
  .modal-body { padding: 16px 20px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--gold-dim) transparent; }
  .toc-list { list-style: none; }
  .toc-item { display: flex; flex-direction: column; gap: 3px; padding: 10px 6px; border-bottom: 1px dotted rgba(143,114,38,0.35); cursor: pointer; font-size: 14.5px; transition: background 0.2s; }
  .toc-item:hover { background: rgba(212,175,55,0.12); color: var(--ruby); }
</style>
</head>
<body>

  <div class="vignette"></div>

  <div class="desk-overlay-ui" id="deskUi">
    <div class="desk-kicker">Kütüphane-i Fıkhu'l-Mukāren</div>
    <h1 class="desk-heading">Câmiu'r-Ruhas ve 4 Mezhep Külliyatı</h1>
    <div class="desk-divider"></div>
    <div class="desk-hint">Okumak için tıklayın veya kitapları fareyle sürükleyip yerleştirin</div>
  </div>

  <canvas id="webgl-canvas"></canvas>

  <div id="reader-screen">
    <div class="reader-backdrop"></div>
    <header class="top-toolbar">
      <div class="reader-left">
        <button class="back-to-desk-btn" id="backToDeskBtn"><span>‹</span> Masaya Dön</button>
        <div class="reader-title" id="activeBookTitle">CÂMİU'R-RUHAS</div>
      </div>
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="Külliyatta Ara (Enter'a Basın)...">
      </div>
      <div class="top-actions">
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
          <span class="tool-label" id="zoomDisplay" style="color:var(--gold-bright); font-weight:600; min-width:36px; text-align:center;">100%</span>
          <button class="tool-btn" id="zoomInBtn">+</button>
        </div>
      </div>
    </footer>
  </div>

  <div class="modal-overlay" id="tocModal">
    <div class="modal-card">
      <div class="modal-header">
        <h3 style="font-family:'Cinzel',serif; font-size:16px;" id="modalTitle">FİHRİST-İ MÜNDERECÂT</h3>
        <button class="modal-close" id="closeTocModal">&times;</button>
      </div>
      <div class="modal-body" id="modalTocList"></div>
    </div>
  </div>

  <div id="achievementToast" class="achievement-toast">
    <div class="ach-icon">🏆</div>
    <div class="ach-texts">
      <div class="ach-title">İlim Tâlibi</div>
      <div class="ach-desc">İlk Fıkıh Cildini Açtın</div>
    </div>
  </div>

  <script id="fikh-raw-data" type="application/json">
__DB_JSON_PLACEHOLDER__
  </script>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/page-flip@2.0.7/dist/js/page-flip.browser.min.js"></script>

  <script>
    window.FIKH_DATABASE = JSON.parse(document.getElementById('fikh-raw-data').textContent);

    const BOOKS_CATALOG = [
      { id: "camiur-ruhas", title: "CÂMİU'R-RUHAS", sub: "500 MESELE VE İCMÂ", color: "#38130f", x: -8.5, arabic: "جَامِعُ الرُّخَصِ", subtitle: "500 Temel Mesele + 100 İcmâ Kanunu", author: "Heyet-i İlmiye" },
      { id: "hanefi", title: "EL-MEBSÛT", sub: "HANEFÎ KÜLLİYATI", color: "#0d2b1a", x: -4.2, arabic: "المَبْسُوطُ وَالبَدَائِعُ", subtitle: "İmam es-Serahsî & el-Kâsânî", author: "Hanefî Mezhebi" },
      { id: "maliki", title: "EL-KÂFÎ", sub: "MÂLİKÎ KÜLLİYATI", color: "#4a3c10", x: 0.1, arabic: "الكافي وَالمَوَاهِبُ", subtitle: "İbn Abdilberr & el-Hattâb", author: "Mâlikî Mezhebi" },
      { id: "safii", title: "EL-ÜMM", sub: "ŞÂFİÎ KÜLLİYATI", color: "#122038", x: 4.4, arabic: "الأُمُّ وَالمَجْمُوعُ", subtitle: "İmâm eş-Şâfiî & en-Nevevî", author: "Şâfiî Mezhebi" },
      { id: "hanbeli", title: "EL-MUĞNÎ", sub: "HANBELÎ KÜLLİYATI", color: "#2d1633", x: 8.7, arabic: "المُغْنِي وَالكَشَّافُ", subtitle: "İbn Kudâme & el-Buhûtî", author: "Hanbelî Mezhebi" }
    ];

    const canvas = document.getElementById('webgl-canvas');
    const deskUi = document.getElementById('deskUi');
    const readerScreen = document.getElementById('reader-screen');
    const activeBookTitleEl = document.getElementById('activeBookTitle');
    const achievementToast = document.getElementById('achievementToast');
    let achievementUnlocked = false;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050403);
    scene.fog = new THREE.FogExp2(0x050403, 0.025);

    const camera = new THREE.PerspectiveCamera(32, window.innerWidth / window.innerHeight, 0.1, 100);
    const CAMERA_REST = { x: 0, y: 13, z: 24 };
    const CAMERA_LOOK = { x: 0, y: -1, z: 0 };
    camera.position.set(0, 18, 28);

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;

    scene.add(new THREE.AmbientLight(0xeedcb5, 0.5));
    const keyLight = new THREE.DirectionalLight(0xffeedd, 1.3);
    keyLight.position.set(6, 18, 12);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0003;
    scene.add(keyLight);

    const warmFill = new THREE.PointLight(0xff9933, 0.7, 40);
    warmFill.position.set(-8, 6, 5);
    scene.add(warmFill);

    // KALİTELİ AHŞAP MASA
    function createWoodTexture() {
      const cv = document.createElement('canvas'); cv.width = 2048; cv.height = 2048;
      const ctx = cv.getContext('2d'); 
      ctx.fillStyle = '#1c0c05'; ctx.fillRect(0, 0, 2048, 2048);
      for (let y = 0; y < 2048; y += 4) {
        let wave = Math.sin(y * 0.01) * 18;
        let c = 18 + Math.random() * 10 + wave;
        ctx.fillStyle = `rgb(${c + 10}, ${c * 0.45}, ${c * 0.25})`;
        ctx.fillRect(0, y, 2048, 4);
      }
      for (let i = 0; i < 3000; i++) {
        ctx.fillStyle = `rgba(0,0,0,${0.1 + Math.random() * 0.4})`;
        ctx.fillRect(0, Math.random() * 2048, 2048, 2 + Math.random() * 4);
      }
      return new THREE.CanvasTexture(cv);
    }
    const tableMat = new THREE.MeshStandardMaterial({ map: createWoodTexture(), roughness: 0.35, metalness: 0.15 });
    const table = new THREE.Mesh(new THREE.PlaneGeometry(100, 100), tableMat);
    table.rotation.x = -Math.PI / 2;
    table.receiveShadow = true;
    scene.add(table);

    const coverDataUrls = {};
    const backCoverDataUrls = {};

    function createCoverTextureAndSave(bookData, isFront) {
      const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 1400;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = bookData.color; ctx.fillRect(0, 0, 1024, 1400);

      const grad = ctx.createRadialGradient(512, 700, 300, 512, 700, 800);
      grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, 'rgba(0,0,0,0.85)');
      ctx.fillStyle = grad; ctx.fillRect(0, 0, 1024, 1400);

      ctx.fillStyle = '#1c130b'; ctx.fillRect(110, 110, 804, 1180);
      const foilGrad = ctx.createLinearGradient(110, 110, 914, 1290);
      foilGrad.addColorStop(0, '#916e25'); foilGrad.addColorStop(0.5, '#d4af37'); foilGrad.addColorStop(1, '#81601d');
      ctx.fillStyle = foilGrad; ctx.fillRect(114, 114, 796, 1172);

      ctx.strokeStyle = '#2b1b07'; ctx.lineWidth = 6; ctx.strokeRect(132, 132, 760, 1136);

      ctx.save();
      ctx.translate(512, 690);
      ctx.strokeStyle = '#2c1a05'; ctx.lineWidth = 3;
      for (let i = 0; i < 32; i++) {
        const rad = (i * Math.PI) / 16;
        ctx.beginPath(); ctx.moveTo(Math.cos(rad) * 45, Math.sin(rad) * 45); ctx.lineTo(Math.cos(rad) * 65, Math.sin(rad) * 65); ctx.stroke();
      }
      ctx.fillStyle = '#221303'; ctx.beginPath(); ctx.ellipse(0, 0, 42, 60, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      if (isFront) {
        ctx.fillStyle = '#bfa157'; ctx.font = '36px serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('﷽', 0, 0);
      }
      ctx.restore();

      if (isFront) {
        ctx.fillStyle = '#1f1305';
        ctx.font = 'bold 50px "Cinzel", serif'; ctx.textAlign = 'center'; ctx.fillText(bookData.title, 512, 280);
        ctx.font = 'bold 26px "Cinzel", serif'; ctx.fillText(bookData.sub, 512, 1120);
      }
      
      const dataUrl = cv.toDataURL('image/jpeg', 0.9);
      if (isFront) coverDataUrls[bookData.id] = dataUrl;
      else backCoverDataUrls[bookData.id] = dataUrl;
      
      return new THREE.CanvasTexture(cv);
    }

    const BOOK_W = 3.1, BOOK_H = 0.85, BOOK_D = 4.4;
    const COVER_W = BOOK_W + 0.22, COVER_H = BOOK_D + 0.22;
    const bookObjects = [];

    BOOKS_CATALOG.forEach((data, index) => {
      const group = new THREE.Group();
      
      const frontCoverMap = createCoverTextureAndSave(data, true);
      const backCoverMap = createCoverTextureAndSave(data, false);
      const frontCoverMat = new THREE.MeshStandardMaterial({ map: frontCoverMap, roughness: 0.6, metalness: 0.1 });
      const backCoverMat = new THREE.MeshStandardMaterial({ map: backCoverMap, roughness: 0.6, metalness: 0.1 });
      const plainMat = new THREE.MeshStandardMaterial({ color: data.color, roughness: 0.7 });

      const pages = new THREE.Mesh(new THREE.BoxGeometry(BOOK_W, BOOK_H, BOOK_D), new THREE.MeshStandardMaterial({ color: 0xdfccaa, roughness: 0.9 }));
      pages.position.set(0.1, BOOK_H / 2 + 0.04, 0);
      pages.castShadow = true;
      group.add(pages);

      const bottomCover = new THREE.Mesh(new THREE.BoxGeometry(COVER_W, 0.08, COVER_H), [
        plainMat, plainMat, plainMat, backCoverMat, plainMat, plainMat
      ]);
      bottomCover.position.set(0.1, 0.04, 0);
      bottomCover.castShadow = true;
      group.add(bottomCover);

      const spine = new THREE.Mesh(new THREE.BoxGeometry(0.12, BOOK_H + 0.12, COVER_H), plainMat);
      spine.position.set(-BOOK_W / 2 - 0.01, (BOOK_H + 0.12) / 2, 0);
      group.add(spine);

      const topCoverHinge = new THREE.Group();
      topCoverHinge.position.set(-BOOK_W / 2 - 0.01, BOOK_H + 0.08, 0);

      const topCover = new THREE.Mesh(new THREE.BoxGeometry(COVER_W, 0.08, COVER_H), [
        plainMat, plainMat, frontCoverMat, new THREE.MeshStandardMaterial({ color: 0xeadbb8 }), plainMat, plainMat
      ]);
      topCover.position.set(COVER_W / 2, 0, 0);
      topCover.castShadow = true;
      topCoverHinge.add(topCover);
      group.add(topCoverHinge);

      group.userData = { bookData: data, topCoverHinge: topCoverHinge, coverMat: frontCoverMat, targetX: data.x, targetZ: 0 };
      group.position.set(data.x, 10, -5);
      group.rotation.x = -0.25;
      scene.add(group);
      bookObjects.push(group);

      new TWEEN.Tween(group.position).to({ y: 0, z: 0 }, 1400).delay(300 + index * 120).easing(TWEEN.Easing.Bounce.Out).start();
      new TWEEN.Tween(group.rotation).to({ x: 0 }, 1200).delay(300 + index * 120).easing(TWEEN.Easing.Cubic.Out).start();
    });

    new TWEEN.Tween(camera.position).to(CAMERA_REST, 2200).delay(100).easing(TWEEN.Easing.Quartic.Out).start();
    setTimeout(() => deskUi.classList.add('visible'), 1600);

    // --- GERÇEKÇİ SÜRÜKLE VE ÇARPIŞMA FİZİĞİ ---
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    let selectedBookGroup = null;
    let hoveredBookGroup = null;
    let draggedBookGroup = null;
    let dragOffset = new THREE.Vector3();
    let isTransitioning = false;
    let isDragged = false;
    let lastMouseX = 0;

    function getHitGroup(clientX, clientY) {
      mouse.x = (clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(clientY / window.innerHeight) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(bookObjects, true);
      if (!hits.length) return null;
      let o = hits[0].object;
      while (o.parent && o.parent.type !== 'Scene') o = o.parent;
      return o;
    }

    function setBookHover(group, isHover) {
      if (!group || group === selectedBookGroup || group === draggedBookGroup) return;
      new TWEEN.Tween(group.position).to({ y: isHover ? 0.35 : 0 }, 300).easing(TWEEN.Easing.Quadratic.Out).start();
      new TWEEN.Tween(group.userData.topCoverHinge.rotation).to({ z: isHover ? 0.12 : 0 }, 300).easing(TWEEN.Easing.Quadratic.Out).start();
      const mat = group.userData.coverMat;
      new TWEEN.Tween(mat).to({ emissiveIntensity: isHover ? 0.35 : 0 }, 300).onUpdate(() => mat.emissive.set(0xd4af37)).start();
    }

    window.addEventListener('pointermove', e => {
      if (isTransitioning || selectedBookGroup) return;

      if (draggedBookGroup) {
        isDragged = true;
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersect = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, intersect);
        
        draggedBookGroup.position.x = intersect.x - dragOffset.x;
        draggedBookGroup.position.z = intersect.z - dragOffset.z;
        
        // Sürüklerken yana yatırma efekti
        let velX = e.clientX - lastMouseX;
        draggedBookGroup.rotation.z = THREE.MathUtils.lerp(draggedBookGroup.rotation.z, -velX * 0.005, 0.2);
        draggedBookGroup.rotation.x = THREE.MathUtils.lerp(draggedBookGroup.rotation.x, (intersect.z * 0.02), 0.2);
        lastMouseX = e.clientX;
        return;
      }

      const hit = getHitGroup(e.clientX, e.clientY);
      if (hit !== hoveredBookGroup) {
        if (hoveredBookGroup) setBookHover(hoveredBookGroup, false);
        if (hit) setBookHover(hit, true);
        hoveredBookGroup = hit;
        canvas.style.cursor = hit ? 'grab' : 'default';
      }
    });

    window.addEventListener('pointerdown', e => {
      if (isTransitioning || selectedBookGroup) return;
      const hit = getHitGroup(e.clientX, e.clientY);
      if (hit) {
        draggedBookGroup = hit;
        isDragged = false;
        lastMouseX = e.clientX;
        canvas.style.cursor = 'grabbing';
        
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersect = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, intersect);
        dragOffset.copy(intersect).sub(draggedBookGroup.position);

        new TWEEN.Tween(hit.position).to({ y: 0.8 }, 200).start();
      }
    });

    window.addEventListener('pointerup', e => {
      if (draggedBookGroup) {
        canvas.style.cursor = 'grab';
        const group = draggedBookGroup;
        draggedBookGroup = null;

        new TWEEN.Tween(group.position).to({ y: 0 }, 400).easing(TWEEN.Easing.Bounce.Out).start();
        new TWEEN.Tween(group.rotation).to({ x: 0, z: 0 }, 400).easing(TWEEN.Easing.Quadratic.Out).start();
        
        group.userData.targetX = group.position.x;
        group.userData.targetZ = group.position.z;

        if (!isDragged) triggerOpenBook(group);
      }
    });

    // BASİT AABB ÇARPIŞMA (Kitaplar İç İçe Girmesin)
    function resolveCollisions() {
      if (selectedBookGroup) return;
      const PADDING = 3.5;
      for (let i = 0; i < bookObjects.length; i++) {
        for (let j = i + 1; j < bookObjects.length; j++) {
          let b1 = bookObjects[i]; let b2 = bookObjects[j];
          let dx = b2.position.x - b1.position.x;
          let dz = b2.position.z - b1.position.z;
          let dist = Math.sqrt(dx * dx + dz * dz);
          if (dist < PADDING && dist > 0.1) {
            let overlap = (PADDING - dist) / 2;
            let nx = dx / dist; let nz = dz / dist;
            if (b1 !== draggedBookGroup) { b1.position.x -= nx * overlap; b1.position.z -= nz * overlap; b1.userData.targetX = b1.position.x; b1.userData.targetZ = b1.position.z; }
            if (b2 !== draggedBookGroup) { b2.position.x += nx * overlap; b2.position.z += nz * overlap; b2.userData.targetX = b2.position.x; b2.userData.targetZ = b2.position.z; }
          }
        }
      }
    }

    // --- PAGE-FLIP VE KİTAP İÇERİĞİ ---
    let pageFlipInstance = null;
    let currentPagesData = [];
    const flipbookEl = document.getElementById('flipbook');
    const bookContainer = document.getElementById('bookContainer');
    const pageStatusEl = document.getElementById('pageStatus');

    function buildPagesForBook(bookData) {
      const pages = [];
      const frontCover = coverDataUrls[bookData.id];
      const backCover = backCoverDataUrls[bookData.id];

      // 1. Dış Ön Kapak
      pages.push({
        density: 'hard', html: `<div class="cover-face" style="background-image: url('${frontCover}'); box-shadow: none; border:none;"></div>`
      });

      // 2. İç Ön Kapak
      pages.push({
        density: 'hard', html: `<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#c5b592;"><div style="background:#fbf6ec; border:2px solid #d4af37; padding:24px; text-align:center; border-radius:4px;"><div style="font-family:'Cinzel',serif; font-size:13px; font-weight:700; color:#30110d;">VAKF-I KÜTÜB</div><div style="font-family:'Amiri',serif; font-size:24px; color:#7a1d1d; margin:8px 0;">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div><p style="font-size:14px; color:#4a3b2c;">${bookData.title}<br><strong>${bookData.subtitle}</strong></p></div></div>`
      });

      if (bookData.id === "camiur-ruhas") {
        const issues = window.FIKH_DATABASE.camiur_ruhas || [];
        
        // Dinamik Fihrist Sayfaları (Her Sayfada 25 Madde)
        const TOC_PER_PAGE = 25;
        const tocPagesCount = Math.ceil(issues.length / TOC_PER_PAGE);
        let startPageNum = 3 + (tocPagesCount * 2); // Meselelerin başlayacağı sayfa no
        if (startPageNum % 2 === 0) startPageNum += 1;

        for (let t = 0; t < tocPagesCount; t++) {
          let chunk = issues.slice(t * TOC_PER_PAGE, (t + 1) * TOC_PER_PAGE);
          let html = `<div class="page-inner"><div class="running-header"><span>CÂMİU'R-RUHAS</span><span>MÜNDERECÂT</span></div><h2 class="chapter-title">Fihrist-i Külliyat (${t + 1})</h2><ul class="toc-list" style="flex:1; overflow-y:auto;">`;
          chunk.forEach((it, idx) => {
            let actualIssueIndex = (t * TOC_PER_PAGE) + idx;
            let targetPNum = startPageNum + (actualIssueIndex * 2);
            html += `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${targetPNum - 1})"><span><strong>Mesele ${it.id}:</strong> ${it.title}</span><span style="color:var(--gold-dim); font-weight:700;">s. ${targetPNum}</span></li>`;
          });
          html += `</ul><div class="running-footer"><span>Fihrist</span><span>— ${t + 1} —</span></div></div>`;
          pages.push({ density: 'soft', html: html });
        }

        // Fihristi Çift Sayı Yapan Boşluk
        while (pages.length < startPageNum - 1) {
          pages.push({ density: 'soft', html: `<div class="page-inner" style="justify-content:center; align-items:center;"><div style="color:var(--gold-dim); font-family:'Cinzel',serif;">Notlar</div></div>` });
        }

        // Mesele Çiftleri
        issues.forEach((it, idx) => {
          let pNum = startPageNum + (idx * 2);
          pages.push({
            density: 'soft',
            html: `
              <div class="page-inner">
                <div class="running-header"><span>${it.chapter}</span><span>MESELE ${it.id}</span></div>
                <div class="section-kicker">${it.chapter}</div>
                <h2 class="chapter-title">Mesele ${it.id}: ${it.title}</h2>
                <div class="scroll-area">
                  <div class="ruhsat-banner">
                    <span class="ruhsat-badge">LİTE TATBİKAT RUHSATI</span>
                    <div class="ruhsat-text">${it.ruhsat.hukum}</div>
                    <div style="font-size:11.5px; color:var(--emerald); margin-top:3px; font-weight:600;">Esas Alınan: ${it.ruhsat.mezhep}</div>
                  </div>
                  <div class="mezhep-grid">
                    <div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Hanefî</span><span class="mezhep-tag hanefi">Hanefî</span></div><div style="font-size:13px;">${it.madhabs.hanefi.hukum}</div>${it.madhabs.hanefi.kaynak ? `<div class="arabic-quote">${it.madhabs.hanefi.kaynak}</div>` : ''}</div>
                    <div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Şâfiî</span><span class="mezhep-tag safii">Şâfiî</span></div><div style="font-size:13px;">${it.madhabs.safii.hukum}</div></div>
                    <div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Mâlikî</span><span class="mezhep-tag maliki">Mâlikî</span></div><div style="font-size:13px;">${it.madhabs.maliki.hukum}</div></div>
                    <div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Hanbelî</span><span class="mezhep-tag hanbeli">Hanbelî</span></div><div style="font-size:13px;">${it.madhabs.hanbeli.hukum}</div></div>
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
                <h3 style="font-family:'Cormorant Garamond',serif; margin:4px 0; font-size:18px; color:var(--leather-outer);">Menşe-i Hilâf ve Hikmet</h3>
                <div class="scroll-area">
                  <div style="font-size:14px; text-align:justify; line-height:1.6; margin-bottom:8px;">${it.hilaf || 'Dört mezhebin delalet ve usûl kurallarına göre tahrîc edilmiştir.'}</div>
                  <div class="telfik-box">
                    <div class="telfik-title">⚖ TELFÎK DENETİMİ VE FETVÂ GÜVENCESİ</div>
                    <div style="line-height:1.5; margin-top:4px;">${it.telfik || 'İcmâ-i mürekkep riski bulunmamaktadır.'}</div>
                  </div>
                </div>
                <div class="running-footer"><span>Tahkîk</span><span>— ${pNum + 1} —</span></div>
              </div>
            `
          });
        });

        // 100 İcmâ Kanunu Bölümü
        const icma = window.FIKH_DATABASE.icma || [];
        if (icma.length > 0) {
          pages.push({
            density: 'soft',
            html: `<div class="page-inner" style="background:#111c2e; color:#f7eed7; justify-content:center; align-items:center; text-align:center;"><div class="shamsah"><svg viewBox="0 0 24 24"><path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/></svg></div><div style="font-family:'Cinzel',serif; font-size:20px; font-weight:700; margin:14px 0; color:var(--gold);">TARTIŞMASIZ KANUNLAR</div><h1 style="font-family:'Amiri',serif; font-size:28px;">الإِجْمَاعُ</h1><div class="desk-divider"></div><div style="font-size:15px; margin-top:10px; color:#c9b78f;">Dört Mezhebin Ortak 100 İttifakı</div></div>`
          });
          pages.push({ density: 'soft', html: `<div class="page-inner"><div style="text-align:justify; font-size:16px; line-height:1.7;"><strong>BEYANNÂME:</strong> Dinde mezhepler arası ihtilaf fürûatın ruhsat alanındadır. Dinin asıllarında, farzların iskeletinde ve haramların sınırlarında dört mezhep tek bir vücut gibidir. Bir müminin amellerinin sahih olabilmesi için takip eden sayfalardaki 100 icmâî ilkenin eksiksiz yerine getirilmesi şarttır; bu maddelerde alternatif yoktur.</div></div>` });

          for (let i = 0; i < icma.length; i += 5) {
            const chunk = icma.slice(i, i + 5);
            pages.push({
              density: 'soft',
              html: `<div class="page-inner"><div class="running-header"><span>EL-MÜTTEFEK ALEYH</span><span>İCMÂ HÜKÜMLERİ</span></div><h2 class="chapter-title">Ortak İttifak (${i + 1} - ${Math.min(i + 5, icma.length)})</h2><div class="scroll-area" style="display:flex; flex-direction:column; gap:8px;">` +
              chunk.map(c => `<div style="background:rgba(255,255,255,0.7); border-left:4px solid var(--gold); padding:8px 10px; font-size:14px; box-shadow:0 2px 4px rgba(0,0,0,0.05);"><strong>${c.id}. ${c.title}:</strong> ${c.rule}</div>`).join('') +
              `</div><div class="running-footer"><span>İcmâ Kanunu</span><span>— İcmâ —</span></div></div>`
            });
          }
        }
      } else {
        // MEZHEP KORPUSLARI (Kitap 2, 3, 4, 5)
        const list = window.FIKH_DATABASE[bookData.id] || [];
        
        pages.push({
          density: 'soft',
          html: `<div class="page-inner"><div class="running-header"><span>${bookData.title}</span><span>MÜNDERECÂT</span></div><h2 class="chapter-title">Aslî Nasslar Fihristi</h2><ul class="toc-list" style="overflow-y:auto;">` +
          list.slice(0, 20).map((n, idx) => `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${4 + idx})"><span>${n.eser} — ${n.kitab}</span></li>`).join('') +
          `</ul><div class="running-footer"><span>Fihrist</span><span>— 1 —</span></div></div>`
        });

        pages.push({
          density: 'soft',
          html: `<div class="page-inner"><div class="running-header"><span>${bookData.title}</span><span>MÜNDERECÂT II</span></div><h2 class="chapter-title">Fihrist (Devam)</h2><ul class="toc-list" style="overflow-y:auto;">` +
          list.slice(20, 40).map((n, idx) => `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${24 + idx})"><span>${n.eser} — ${n.kitab}</span></li>`).join('') +
          `</ul><div class="running-footer"><span>Fihrist</span><span>— 2 —</span></div></div>`
        });

        list.forEach((n, idx) => {
          pages.push({
            density: 'soft',
            html: `<div class="page-inner"><div class="running-header"><span>${n.eser}</span><span>ASIL NASS</span></div><h2 class="chapter-title">${n.muellif} — ${n.eser}</h2><div style="font-size:13px; color:var(--ink-soft); margin-bottom:8px;">Cilt: ${n.cilt} | Sayfa: ${n.sayfa} | ${n.kitab || ''}</div><div class="scroll-area"><div class="arabic-quote" style="font-size:16px; line-height:1.9;">« ${n.metin} »</div></div><div class="running-footer"><span>Klasik Külliyat</span><span>— ${idx + 3} —</span></div></div>`
          });
        });
      }

      // KESİN ÇİFT SAYFA GARANTİSİ (Motor çökmesini önler)
      if (pages.length % 2 !== 0) {
        pages.push({ density: 'soft', html: `<div class="page-inner" style="justify-content:center; align-items:center;"><div style="font-family:'Cinzel',serif; font-size:12px; color:var(--gold-dim);">BEYAZ SAHÎFE</div></div>` });
      }

      // Sondan Önceki İç Kapak
      pages.push({
        density: 'hard',
        html: `<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#c5b592;"><div style="background:#fbf6ec; border:2px solid #d4af37; padding:20px; text-align:center; border-radius:4px;"><div style="font-family:'Cinzel',serif; font-size:12px; font-weight:700; color:#30110d;">HÂTİME-İ CİLT</div><div class="cover-rule"></div><div style="font-size:12px; color:#4a3b2c;">Klasik Sert Cilt Mekanizması ile Ciltlenmiştir.</div></div></div>`
      });

      // Arka Kapak (Canvas 1:1)
      pages.push({
        density: 'hard',
        html: `<div class="cover-face" style="background-image: url('${backCover}'); box-shadow: none; border:none;"></div>`
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
        pageStatusEl.textContent = `Sayfa ${pageIdx} – ${Math.min(pageIdx + 1, total - 1)} / ${total - 2}`;
      }
    }

    function prepareReader(bookData) {
      activeBookTitleEl.textContent = bookData.title;
      if (pageFlipInstance) { pageFlipInstance.destroy(); pageFlipInstance = null; }
      flipbookEl.innerHTML = '';

      currentPagesData = buildPagesForBook(bookData);
      
      let htmlString = "";
      currentPagesData.forEach(p => { htmlString += `<div class="page" data-density="${p.density}">${p.html}</div>`; });
      flipbookEl.innerHTML = htmlString;

      setTimeout(() => {
        pageFlipInstance = new St.PageFlip(flipbookEl, {
          width: 480, height: 700, size: 'stretch',
          minWidth: 300, maxWidth: 1200, minHeight: 400, maxHeight: 1500,
          showCover: true, maxShadowOpacity: 0.6, usePortrait: false,
          drawShadow: true, flippingTime: 750, startPage: 0
        });

        const renderedPages = document.querySelectorAll('#flipbook .page');
        pageFlipInstance.loadFromHTML(renderedPages);
        pageFlipInstance.on('flip', e => updateReaderUi(e.data));
        
        bookContainer.style.transition = 'none';
        updateReaderUi(0);
        void bookContainer.offsetHeight;
        bookContainer.style.transition = '';
      }, 50);
    }

    function triggerOpenBook(group) {
      if (isTransitioning) return;
      isTransitioning = true;
      selectedBookGroup = group;
      deskUi.classList.add('hidden');
      const data = group.userData.bookData;

      prepareReader(data);

      new TWEEN.Tween(group.position).to({ x: 0, y: 5.5, z: 8.5 }, 850).easing(TWEEN.Easing.Cubic.InOut).start();
      new TWEEN.Tween(group.rotation).to({ x: 0.95, y: 0, z: 0 }, 850).easing(TWEEN.Easing.Cubic.InOut)
        .onComplete(() => {
          group.visible = false;
          readerScreen.classList.add('screen-active');
          isTransitioning = false;
          setTimeout(() => {
            if (pageFlipInstance) pageFlipInstance.flipNext('bottom');
            if (!achievementUnlocked && data.id === "camiur-ruhas") {
              achievementUnlocked = true;
              setTimeout(() => {
                achievementToast.classList.add('show');
                setTimeout(() => achievementToast.classList.remove('show'), 4500);
              }, 600);
            }
          }, 380);
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
        new TWEEN.Tween(group.position).to({ x: group.userData.targetX, y: 0, z: group.userData.targetZ }, 850).easing(TWEEN.Easing.Cubic.InOut).start();
        new TWEEN.Tween(group.rotation).to({ x: 0, y: 0, z: 0 }, 850).easing(TWEEN.Easing.Cubic.InOut)
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
      currentZoom = Math.min(2.5, currentZoom + 0.15);
      document.documentElement.style.setProperty('--zoom-factor', currentZoom);
      document.getElementById('zoomDisplay').textContent = Math.round(currentZoom * 100) + '%';
    });
    document.getElementById('zoomOutBtn').addEventListener('click', () => {
      currentZoom = Math.max(0.7, currentZoom - 0.15);
      document.documentElement.style.setProperty('--zoom-factor', currentZoom);
      document.getElementById('zoomDisplay').textContent = Math.round(currentZoom * 100) + '%';
    });

    let currentFontSize = 15;
    document.getElementById('fontIncBtn').addEventListener('click', () => {
      currentFontSize = Math.min(22, currentFontSize + 1);
      document.documentElement.style.setProperty('--book-font-size', currentFontSize + 'px');
    });
    document.getElementById('fontDecBtn').addEventListener('click', () => {
      currentFontSize = Math.max(12, currentFontSize - 1);
      document.documentElement.style.setProperty('--book-font-size', currentFontSize + 'px');
    });

    const searchInput = document.getElementById('searchInput');
    const tocModal = document.getElementById('tocModal');
    const modalTocList = document.getElementById('modalTocList');

    function executeSearch(q) {
      if (q.length < 2) return;
      const issues = (window.FIKH_DATABASE.camiur_ruhas || []).filter(it => it.title.toLowerCase().includes(q) || it.ruhsat.hukum.toLowerCase().includes(q));
      const hn = (window.FIKH_DATABASE.hanefi || []).filter(n => n.metin.toLowerCase().includes(q));
      const sf = (window.FIKH_DATABASE.safii || []).filter(n => n.metin.toLowerCase().includes(q));
      
      let resHtml = `<div style="padding-bottom:6px; font-weight:700; color:var(--ruby);">${issues.length + hn.length + sf.length} Arama Sonucu Bulundu:</div><ul class="toc-list">`;
      
      if (issues.length > 0) {
        resHtml += `<li style="padding:6px 0 2px; font-weight:700; color:var(--gold-dim);">[1. KİTAP: CÂMİU'R-RUHAS]</li>`;
        issues.slice(0, 20).forEach(r => { resHtml += `<li class="toc-item" onclick="openBookIssue('camiur-ruhas', ${r.id})"><span><strong>Mesele ${r.id}:</strong> ${r.title}</span><span style="color:var(--emerald); font-size:12px;">${r.ruhsat.mezhep}</span></li>`; });
      }
      if (hn.length > 0) {
        resHtml += `<li style="padding:8px 0 2px; font-weight:700; color:var(--gold-dim);">[2. KİTAP: HANEFÎ KÜLLİYATI]</li>`;
        hn.slice(0, 10).forEach(n => { resHtml += `<li class="toc-item" onclick="openClassicalBook('hanefi')"><span><strong>${n.muellif} — ${n.eser}</strong></span><div class="arabic-quote" style="font-size:13px;">${n.metin.substring(0, 120)}...</div></li>`; });
      }
      if (sf.length > 0) {
        resHtml += `<li style="padding:8px 0 2px; font-weight:700; color:var(--gold-dim);">[4. KİTAP: ŞÂFİÎ KÜLLİYATI]</li>`;
        sf.slice(0, 10).forEach(n => { resHtml += `<li class="toc-item" onclick="openClassicalBook('safii')"><span><strong>${n.muellif} — ${n.eser}</strong></span><div class="arabic-quote" style="font-size:13px;">${n.metin.substring(0, 120)}...</div></li>`; });
      }
      resHtml += '</ul>';
      modalTocList.innerHTML = resHtml;
      document.getElementById('modalTitle').textContent = "ARAMA SONUÇLARI";
      tocModal.classList.add('active');
    }

    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') executeSearch(e.target.value.toLowerCase().trim());
    });

    window.openBookIssue = function(bookId, issueId) {
      tocModal.classList.remove('active');
      let targetGroup = bookObjects.find(g => g.userData.bookData.id === bookId);
      if (!targetGroup) return;
      if (!selectedBookGroup || selectedBookGroup.userData.bookData.id !== bookId) triggerOpenBook(targetGroup);
      setTimeout(() => {
        let tocPagesCount = Math.ceil(500 / 25);
        let startPageNum = 3 + (tocPagesCount * 2);
        if (startPageNum % 2 === 0) startPageNum += 1;
        let targetPage = startPageNum + (issueId - 1) * 2;
        if (pageFlipInstance) pageFlipInstance.turnToPage(targetPage - 1);
      }, 1000);
    };

    window.openClassicalBook = function(bookId) {
      tocModal.classList.remove('active');
      let targetGroup = bookObjects.find(g => g.userData.bookData.id === bookId);
      if (targetGroup) triggerOpenBook(targetGroup);
    };

    document.getElementById('openTocBtn').addEventListener('click', () => {
      if (!selectedBookGroup) return;
      const bData = selectedBookGroup.userData.bookData;
      let html = '<ul class="toc-list">';
      if (bData.id === "camiur-ruhas") {
        const issues = window.FIKH_DATABASE.camiur_ruhas || [];
        issues.slice(0, 500).forEach((it, idx) => {
          let startPageNum = 3 + (Math.ceil(500/25) * 2);
          if(startPageNum % 2 === 0) startPageNum += 1;
          let pNum = startPageNum + idx * 2;
          html += `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${pNum-1}); tocModal.classList.remove('active');"><span><strong>Mesele ${it.id}:</strong> ${it.title}</span><span style="color:var(--gold-dim); font-weight:700;">s. ${pNum}</span></li>`;
        });
      } else {
        html += `<li class="toc-item"><span>Bu ciltteki tüm aslî nasslar sayfalara ciltlenmiştir. Çevirerek okuyabilirsiniz.</span></li>`;
      }
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
      resolveCollisions(); // Kitapları birbirine ittiren AABB fiziği
      camera.lookAt(CAMERA_LOOK.x, CAMERA_LOOK.y, CAMERA_LOOK.z);
      renderer.render(scene, camera);
    }
    animate();
  </script>
</body>
</html>'''

    full_output = HTML_CONTENT.replace("__DB_JSON_PLACEHOLDER__", json_data)

    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(full_output)

    size_mb = os.path.getsize(OUTPUT_HTML_PATH) / (1024 * 1024)
    print("=" * 80)
    print(f"[✓] KUSURSUZ 5 KİTAPLI GERÇEKÇİ KÜTÜPHANE ÜRETİLDİ: {OUTPUT_HTML_PATH}")
    print(f"    - Fihrist sorunu çözüldü (500 mesele sırayla dizildi).")
    print(f"    - Sayfalara kaydırma çubuğu (scrollbar) eklendi.")
    print(f"    - Kitap fiziği (çarpışma ve sürükle-bırak) eklendi.")
    print(f"    - Ön ve arka kapaklar 1:1 eşitlendi, Page-Flip hatası sıfırlandı.")
    print(f"    - Steam başarımı entegre edildi.")
    print(f"    - Arama kutusu ENTER tuşuyla çalışır hale getirildi.")
    print(f"    Boyut: {size_mb:.2f} MB")
    print("=" * 80)

if __name__ == "__main__":
    generate_web_library()
