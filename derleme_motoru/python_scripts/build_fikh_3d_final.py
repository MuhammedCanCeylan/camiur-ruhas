import os
import re
import json
import sqlite3

MASTER_MD_PATH = r"D:\fikh_kitap\Camiur_Ruhas_Nihai_Kulliyat.md"
DB_PATH = os.path.join("metadata", "fikh_corpus.db")
OUTPUT_HTML_PATH = r"D:\fikh_kitap\index.html"

def extract_corpus_by_madhab(db_path, limit=500):
    print("[*] Klasik Asıl Kitaplar (SQLite Corpus) taranıyor...")
    if not os.path.exists(db_path):
        return [], []
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Hanefi & Maliki (Kitap 2)
    cur.execute("""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE mezhep IN ('Hanefi', 'Maliki') AND metin_orijinal IS NOT NULL AND LENGTH(metin_orijinal) > 40
        LIMIT ?;
    """, (limit,))
    rows_hm = cur.fetchall()
    
    # Safii & Hanbeli (Kitap 3)
    cur.execute("""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE mezhep IN ('Safii', 'Hanbeli') AND metin_orijinal IS NOT NULL AND LENGTH(metin_orijinal) > 40
        LIMIT ?;
    """, (limit,))
    rows_sh = cur.fetchall()
    
    def format_rows(rows):
        res = []
        for r in rows:
            res.append({
                "id": r[0], "mezhep": r[1], "muellif": r[2], "eser": r[3],
                "cilt": r[4], "sayfa": r[5], "kitab": r[6], "bab": r[7],
                "metin": r[8][:400].replace("\n", " ").strip() + "..."
            })
        return res

    return format_rows(rows_hm), format_rows(rows_sh)

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
        chap_name = chap_match.group(1).strip() if chap_match else "FIKIH"

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
            return {"hukum": "", "kaynak": ""}

        hilaf_match = re.search(r"## 3\. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\s*\n([\s\S]*?)(?=\n## 4\.|$)", block)
        hilaf = hilaf_match.group(1).strip() if hilaf_match else ""

        telfik_match = re.search(r"## 4\. TELFÎK DENETİMİ VE FETVÂ\s*\n([\s\S]*?)(?=\n---|$)", block)
        telfik = telfik_match.group(1).strip() if telfik_match else ""

        issues_list.append({
            "id": m_id,
            "chapter": chap_name,
            "title": m_title,
            "ruhsat": {"hukum": ruhsat_hukum, "mezhep": ruhsat_mezhep},
            "madhabs": {
                "hanefi": extract_madhab("Hanefî"),
                "safii": extract_madhab("Şâfiî"),
                "maliki": extract_madhab("Mâlikî"),
                "hanbeli": extract_madhab("Hanbelî")
            },
            "hilaf": hilaf,
            "telfik": telfik
        })

    # Sıralama hatasını (1, 2, 41...) Python tarafında kesin olarak çözüyoruz
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

    print(f"[+] Doğrulandı: {len(issues_list)} Mesele (Sıralı) | {len(icma_list)} İcmâ Kanunu")
    return issues_list, icma_list

def generate_web_library():
    issues, icma = parse_master_manuscript(MASTER_MD_PATH)
    corpus_hm, corpus_sh = extract_corpus_by_madhab(DB_PATH)

    full_payload = {
        "camiur_ruhas": issues,
        "icma": icma,
        "corpus_hm": corpus_hm,
        "corpus_sh": corpus_sh
    }
    json_data = json.dumps(full_payload, ensure_ascii=False).replace("</script>", "<\\/script>")

    HTML_HEAD = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CÂMİU'R-RUHAS VE ASLÎ FIKIH KÜLLİYATI — 3D Masa</title>

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
    --book-font-size: 14.5px;
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

  .stf__parent { position: relative; display: block; box-sizing: border-box; transform-style: preserve-3d; }
  .stf__wrapper { position: relative; width: 100%; height: 100%; box-sizing: border-box; }
  .stf__block { position: absolute; width: 100%; height: 100%; box-sizing: border-box; }
  .stf__item { display: none; position: absolute; transform-style: preserve-3d; }
  .stf__item.--active { display: block; }

  #webgl-canvas {
    position: fixed; inset: 0; width: 100vw; height: 100vh; display: block; z-index: 1;
  }

  /* Buhar/Sis Efekti CSS (Opsiyonel Derinlik) */
  .vignette {
    position: fixed; inset: 0; z-index: 2; pointer-events: none;
    background: radial-gradient(circle at center, transparent 40%, rgba(5,4,3,0.85) 100%);
  }

  /* Steam Benzeri Başarım Bildirimi */
  .achievement-toast {
    position: fixed; bottom: -80px; right: 20px; z-index: 1000;
    background: linear-gradient(135deg, #1b2838 0%, #2a475e 100%);
    border: 1px solid #171a21; border-radius: 4px; padding: 12px 16px;
    display: flex; align-items: center; gap: 14px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.6);
    transition: transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    color: #c7d5e0; font-family: sans-serif;
  }
  .achievement-toast.show { transform: translateY(-100px); }
  .ach-icon {
    width: 44px; height: 44px; background: #d4af37; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 24px;
    box-shadow: 0 0 10px rgba(212,175,55,0.5);
  }
  .ach-texts { display: flex; flex-direction: column; }
  .ach-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #66c0f4; margin-bottom: 3px; }
  .ach-desc { font-size: 14px; font-weight: bold; color: #fff; }

  .desk-overlay-ui {
    position: fixed; top: 24px; left: 0; right: 0; display: flex; flex-direction: column; align-items: center;
    pointer-events: none; z-index: 10; opacity: 0; transform: translateY(-16px);
    transition: opacity 0.7s cubic-bezier(0.22,1,0.36,1), transform 0.7s cubic-bezier(0.22,1,0.36,1);
  }
  .desk-overlay-ui.visible { opacity: 1; transform: translateY(0); }
  .desk-overlay-ui.hidden { opacity: 0; transform: translateY(-16px); }
  .desk-kicker { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.35em; color: var(--gold); text-transform: uppercase; margin-bottom: 4px; text-shadow: 0 2px 4px #000; }
  .desk-heading { font-family: 'Cormorant Garamond', serif; font-size: 32px; color: #fdf6e6; font-weight: 700; letter-spacing: 0.05em; text-shadow: 0 3px 8px #000; }
  .desk-divider { width: 80px; height: 1.5px; background: linear-gradient(90deg, transparent, var(--gold), transparent); margin: 8px auto 0; }
  .desk-hint { color: #c5ad88; font-size: 13.5px; font-style: italic; margin-top: 6px; text-shadow: 0 2px 4px #000; }

  #reader-screen { position: fixed; inset: 0; z-index: 20; opacity: 0; pointer-events: none; }
  #reader-screen.screen-active { opacity: 1; pointer-events: auto; }
  .reader-backdrop { position: absolute; inset: 0; z-index: 0; background: radial-gradient(circle at 50% 45%, rgba(13,9,6,0.76) 0%, rgba(5,4,3,0.98) 100%); opacity: 0; transition: opacity 0.75s ease; pointer-events: none; }
  #reader-screen.screen-active .reader-backdrop { opacity: 1; }

  .top-toolbar {
    position: absolute; top: 0; left: 0; right: 0; height: 52px; background: linear-gradient(180deg, rgba(16,11,8,0.96) 0%, rgba(24,16,12,0.88) 100%);
    border-bottom: 1px solid rgba(212,175,55,0.25); display: flex; align-items: center; justify-content: space-between;
    padding: 0 20px; z-index: 50; backdrop-filter: blur(8px); font-family: 'Cormorant Garamond', serif;
    opacity: 0; transition: opacity 0.55s ease 0.15s;
  }
  #reader-screen.screen-active .top-toolbar { opacity: 1; }
  .reader-left { display: flex; align-items: center; gap: 14px; }
  .back-to-desk-btn { background: rgba(212,175,55,0.18); border: 1px solid rgba(212,175,55,0.5); color: #f7eed7; padding: 6px 14px; border-radius: 20px; font-family: 'Cormorant Garamond', serif; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
  .back-to-desk-btn:hover { background: rgba(212,175,55,0.35); color: #fff; transform: translateX(-2px); }
  .reader-title { color: #f1e4c7; font-size: 17px; font-weight: 700; letter-spacing: 0.05em; }

  .search-box { display: flex; align-items: center; background: rgba(0,0,0,0.45); border: 1px solid rgba(212,175,55,0.35); border-radius: 20px; padding: 4px 14px; }
  .search-box input { background: transparent; border: none; outline: none; color: #fdf6e6; font-family: 'Crimson Pro', serif; font-size: 13.5px; width: 230px; }
  .search-box input::placeholder { color: rgba(212,175,55,0.5); font-style: italic; }

  .top-actions { display: flex; align-items: center; gap: 8px; }
  .action-btn { background: rgba(233,220,192,0.08); border: 1px solid rgba(212,175,55,0.35); color: #efe2c4; padding: 5px 12px; border-radius: 6px; font-family: 'Cormorant Garamond', serif; font-size: 13.5px; cursor: pointer; }
  .action-btn:hover { background: rgba(212,175,55,0.22); color: #fff; }

  .viewport { position: absolute; inset: 52px 0 60px 0; display: flex; align-items: center; justify-content: center; perspective: 2600px; overflow: hidden; z-index: 1; }
  .book-container { position: relative; width: calc(var(--page-w) * 2); height: var(--page-h); transform-style: preserve-3d; transform: translateX(0) scale(var(--zoom-factor, 1.0)); transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1); }
  .book-container.is-cover-closed { transform: translateX(calc(var(--page-w) * -0.5)) scale(var(--zoom-factor, 1.0)); }
  .book-container.is-back-closed { transform: translateX(calc(var(--page-w) * 0.5)) scale(var(--zoom-factor, 1.0)); }

  .book-shadow { position: absolute; left: 50%; bottom: -30px; transform: translateX(-50%); width: 92%; height: 46px; background: radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, transparent 75%); filter: blur(6px); pointer-events: none; z-index: 1; }
  #flipbook { width: calc(var(--page-w) * 2); height: var(--page-h); margin: 0 auto; }

  .page { width: 100%; height: 100%; background-color: var(--paper); overflow: hidden; }
  .page[data-density="hard"] { background-color: var(--leather-dark); }
  .cover-face { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 34px 26px; text-align: center; border: 2px solid rgba(212,175,55,0.45); position: relative; box-shadow: inset 0 0 32px rgba(0,0,0,0.85); background-size: cover; background-position: center; }
  .cover-face::before { content: ""; position: absolute; inset: 10px; border: 1.5px solid rgba(212,175,55,0.65); }

  .shamsah { width: 78px; height: 78px; border-radius: 50%; border: 2px solid var(--gold); display: flex; align-items: center; justify-content: center; margin-bottom: 14px; background: radial-gradient(circle, rgba(212,175,55,0.2) 0%, rgba(0,0,0,0.4) 100%); }
  .shamsah svg { width: 44px; height: 44px; fill: var(--gold); }
  .cover-kicker { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 0.35em; color: var(--gold); margin-bottom: 6px; }
  .cover-title-ar { font-family: 'Amiri', serif; font-size: 26px; font-weight: 700; color: var(--gold-bright); direction: rtl; }
  .cover-title-tr { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 22px; color: #f7eed7; margin-bottom: 6px; }
  .cover-rule { width: 60px; height: 1.5px; background: linear-gradient(90deg, transparent, var(--gold), transparent); margin: 8px auto 12px; }
  .cover-subtitle { font-family: 'Crimson Pro', serif; font-style: italic; font-size: 13.5px; color: #c9b78f; line-height: 1.4; }
  .cover-author { font-family: 'Cormorant Garamond', serif; font-size: 13px; color: var(--gold); letter-spacing: 0.15em; margin-top: 14px; }

  .page-inner { width: 100%; height: 100%; display: flex; flex-direction: column; padding: 24px 22px 18px; position: relative; font-size: var(--book-font-size); line-height: 1.55; color: var(--ink); user-select: text; }
  .page-inner::after { content: ""; position: absolute; inset: 10px; border: 1px solid rgba(212,175,55,0.45); pointer-events: none; }
  .running-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(143,114,38,0.35); padding-bottom: 4px; margin-bottom: 8px; font-family: 'Cormorant Garamond', serif; font-size: 11.5px; color: var(--ink-dim); }
  .running-footer { margin-top: auto; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(143,114,38,0.25); padding-top: 4px; font-family: 'Cormorant Garamond', serif; font-size: 12px; color: var(--ink-dim); }
  .section-kicker { font-family: 'Cinzel', serif; font-size: 9.5px; letter-spacing: 0.2em; color: var(--gold-dim); font-weight: 700; }
  .chapter-title { font-family: 'Cormorant Garamond', serif; font-size: 17px; font-weight: 700; color: var(--ruby); margin-bottom: 6px; border-bottom: 1px solid rgba(122,29,29,0.18); padding-bottom: 3px; }

  .ruhsat-banner { background: linear-gradient(135deg, rgba(28,82,52,0.08), rgba(212,175,55,0.12)); border: 1px solid rgba(28,82,52,0.45); border-left: 4px solid var(--emerald); padding: 6px 9px; margin: 5px 0; border-radius: 0 4px 4px 0; }
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
  .arabic-quote { font-family: 'Amiri', serif; direction: rtl; font-size: 14px; color: #3b2a1a; background: rgba(212,175,55,0.08); padding: 2px 6px; border-radius: 3px; border-right: 2px solid var(--gold); margin-top: 2px; }
  .telfik-box { background: rgba(122,29,29,0.06); border: 1px dashed rgba(122,29,29,0.4); padding: 5px 7px; border-radius: 3px; margin-top: 5px; font-size: 12.5px; }
  .telfik-title { font-weight: 700; color: var(--ruby); font-family: 'Cinzel', serif; font-size: 9px; }

  .bottom-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 60px; background: linear-gradient(0deg, rgba(16,11,8,0.96) 0%, rgba(24,16,12,0.88) 100%); border-top: 1px solid rgba(212,175,55,0.25); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 50; backdrop-filter: blur(8px); font-family: 'Cormorant Garamond', serif; opacity: 0; transition: opacity 0.55s ease 0.15s; }
  #reader-screen.screen-active .bottom-bar { opacity: 1; }
  .nav-group { display: flex; align-items: center; gap: 8px; }
  .nav-btn { background: rgba(233,220,192,0.08); border: 1px solid rgba(212,175,55,0.35); color: #efe2c4; width: 34px; height: 34px; border-radius: 50%; font-size: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
  .nav-btn:hover { background: rgba(212,175,55,0.25); color: #fff; }
  .page-status { color: #eeddbb; font-size: 14px; min-width: 140px; text-align: center; font-style: italic; }
  .cover-toggle-btn { background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(122,29,29,0.3)); border: 1px solid var(--gold); color: #f7eed7; font-weight: 600; padding: 4px 11px; border-radius: 16px; cursor: pointer; font-size: 12px; }

  .tool-group { display: flex; align-items: center; gap: 10px; }
  .tool-subgroup { display: flex; align-items: center; gap: 4px; background: rgba(0,0,0,0.3); padding: 3px 7px; border-radius: 16px; border: 1px solid rgba(212,175,55,0.2); }
  .tool-label { font-size: 11.5px; color: #bfa886; }
  .tool-btn { background: rgba(233,220,192,0.1); border: 1px solid rgba(212,175,55,0.25); color: #f3e5c8; min-width: 24px; height: 24px; border-radius: 12px; font-size: 12px; cursor: pointer; }

  .modal-overlay { position: fixed; inset: 0; background: rgba(10,6,4,0.8); backdrop-filter: blur(5px); display: none; align-items: center; justify-content: center; z-index: 100; }
  .modal-overlay.active { display: flex; }
  .modal-card { background: #fbf6ec; border: 2px solid var(--gold); border-radius: 6px; width: 90%; max-width: 720px; max-height: 84vh; display: flex; flex-direction: column; }
  .modal-header { background: var(--leather-dark); color: var(--gold); padding: 12px 18px; border-bottom: 2px solid var(--gold); display: flex; align-items: center; justify-content: space-between; }
  .modal-close { background: none; border: none; color: #f5eed8; font-size: 20px; cursor: pointer; }
  .modal-body { padding: 14px 18px; overflow-y: auto; }
  .toc-list { list-style: none; }
  .toc-item { display: flex; flex-direction: column; gap: 2px; padding: 8px 4px; border-bottom: 1px dotted rgba(143,114,38,0.3); cursor: pointer; font-size: 13.5px; }
  .toc-item:hover { background: rgba(212,175,55,0.15); color: var(--ruby); }
</style>
</head>
<body>

  <div class="vignette"></div>

  <div class="desk-overlay-ui" id="deskUi">
    <div class="desk-kicker">Kütüphane-i Fıkhu'l-Mukāren</div>
    <h1 class="desk-heading">Câmiu'r-Ruhas ve Aslî Külliyat</h1>
    <div class="desk-divider"></div>
    <div class="desk-hint">Açmak için tıklayın veya kitapları fareyle sürükleyin</div>
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

  <!-- STEAM BAŞARIMI BİLDİRİMİ -->
  <div id="achievementToast" class="achievement-toast">
    <div class="ach-icon">🏆</div>
    <div class="ach-texts">
      <div class="ach-title">BAŞARIM KAZANILDI</div>
      <div class="ach-desc">İlim Tâlibi: İlk Fıkıh Cildini Açtın</div>
    </div>
  </div>

  <!-- TAM GÖMÜLÜ VERİTABANI KAPSÜLÜ -->
  <script id="fikh-raw-data" type="application/json">
'''

    HTML_TAIL = r'''
  </script>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/page-flip@2.0.7/dist/js/page-flip.browser.min.js"></script>

  <script>
    window.FIKH_DATABASE = JSON.parse(document.getElementById('fikh-raw-data').textContent);

    const BOOKS_CATALOG = [
      {
        id: "camiur-ruhas",
        title: "CÂMİU'R-RUHAS",
        sub: "500 MESELE VE İCMÂ",
        color: "#38130f",
        x: -4.5,
        arabic: "جَامِعُ الرُّخَصِ وَالتَّحْقِيق",
        subtitle: "500 Temel ve Çağdaş Mesele + 100 İcmâ Kanunnamesi",
        author: "Müellefât-ı Fıkhu'l-Mukāren",
        theme: { leather: "#38130f", leatherDark: "#1a0806" }
      },
      {
        id: "kitabul-asl",
        title: "EL-ASL VE'L-MEBSÛT",
        sub: "HANEFÎ & MÂLİKÎ KÜLLİYATI",
        color: "#0d2b1a",
        x: 0,
        arabic: "الأَصْلُ وَالمَبْسُوطُ وَالكافي",
        subtitle: "es-Serahsî, el-Kâsânî ve İbn Abdilberr Aslî Nassları",
        author: "Metûn-i Kadîme (Cild I)",
        theme: { leather: "#0d2b1a", leatherDark: "#06150d" }
      },
      {
        id: "kitabul-umm",
        title: "EL-ÜMM VE'L-MUĞNÎ",
        sub: "ŞÂFİÎ & HANBELÎ KÜLLİYATI",
        color: "#122038",
        x: 4.5,
        arabic: "الأُمُّ وَالمَجْمُوعُ وَالمُغْنِي",
        subtitle: "İmâm eş-Şâfiî, en-Nevevî ve İbn Kudâme Aslî Nassları",
        author: "Metûn-i Kadîme (Cild II)",
        theme: { leather: "#122038", leatherDark: "#09101d" }
      }
    ];

    const canvas = document.getElementById('webgl-canvas');
    const deskUi = document.getElementById('deskUi');
    const readerScreen = document.getElementById('reader-screen');
    const activeBookTitleEl = document.getElementById('activeBookTitle');
    const achievementToast = document.getElementById('achievementToast');
    let achievementUnlocked = false;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050403);
    scene.fog = new THREE.FogExp2(0x050403, 0.035);

    const camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100);
    const CAMERA_REST = { x: 0, y: 11, z: 14 };
    const CAMERA_LOOK = { x: 0, y: 0, z: 0 };
    camera.position.set(0, 16, 22);

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;

    scene.add(new THREE.AmbientLight(0xeedcb5, 0.45));
    const keyLight = new THREE.DirectionalLight(0xffeedd, 1.2);
    keyLight.position.set(5, 15, 10);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0005;
    scene.add(keyLight);

    const warmFill = new THREE.PointLight(0xff9933, 0.6, 30);
    warmFill.position.set(-6, 5, 4);
    scene.add(warmFill);

    // KALİTELİ AHŞAP MASA (Procedural Texture)
    function createWoodTexture() {
      const cv = document.createElement('canvas'); cv.width = 2048; cv.height = 2048;
      const ctx = cv.getContext('2d'); 
      ctx.fillStyle = '#1c0c05'; ctx.fillRect(0, 0, 2048, 2048);
      for (let y = 0; y < 2048; y += 4) {
        let wave = Math.sin(y * 0.015) * 15;
        let c = 20 + Math.random() * 8 + wave;
        ctx.fillStyle = `rgb(${c + 8}, ${c * 0.5}, ${c * 0.3})`;
        ctx.fillRect(0, y, 2048, 4);
      }
      for (let i = 0; i < 2000; i++) {
        ctx.fillStyle = `rgba(0,0,0,${0.1 + Math.random() * 0.3})`;
        ctx.fillRect(0, Math.random() * 2048, 2048, 2 + Math.random() * 3);
      }
      return new THREE.CanvasTexture(cv);
    }
    const tableMat = new THREE.MeshStandardMaterial({ map: createWoodTexture(), roughness: 0.4, metalness: 0.1 });
    const table = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), tableMat);
    table.rotation.x = -Math.PI / 2;
    table.receiveShadow = true;
    scene.add(table);

    // 1:1 EŞLEŞEN KAPAK ÇİZERİ (HEM 3D HEM 2D HTML İÇİN)
    const coverDataUrls = {};
    function createCoverTextureAndSave(bookData) {
      const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 1400;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = bookData.color; ctx.fillRect(0, 0, 1024, 1400);

      const grad = ctx.createRadialGradient(512, 700, 280, 512, 700, 750);
      grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, 'rgba(0,0,0,0.75)');
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
      ctx.fillStyle = '#bfa157'; ctx.font = '36px serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('﷽', 0, 0);
      ctx.restore();

      ctx.fillStyle = '#1f1305';
      ctx.font = 'bold 50px "Cinzel", serif'; ctx.textAlign = 'center'; ctx.fillText(bookData.title, 512, 280);
      ctx.font = 'bold 28px "Cinzel", serif'; ctx.fillText(bookData.sub, 512, 1110);
      
      const tex = new THREE.CanvasTexture(cv);
      coverDataUrls[bookData.id] = cv.toDataURL('image/png'); // 2D DOM İçin Kaydet
      return tex;
    }

    const BOOK_W = 2.8, BOOK_H = 0.8, BOOK_D = 4.0;
    const COVER_W = BOOK_W + 0.22, COVER_H = BOOK_D + 0.22;
    const bookObjects = [];

    BOOKS_CATALOG.forEach((data, index) => {
      const group = new THREE.Group();
      
      const coverMap = createCoverTextureAndSave(data);
      const coverMat = new THREE.MeshStandardMaterial({ map: coverMap, roughness: 0.65, metalness: 0.1 });
      const plainMat = new THREE.MeshStandardMaterial({ color: data.color, roughness: 0.7 });

      const pages = new THREE.Mesh(new THREE.BoxGeometry(BOOK_W, BOOK_H, BOOK_D), new THREE.MeshStandardMaterial({ color: 0xdfccaa, roughness: 0.9 }));
      pages.position.set(0.1, BOOK_H / 2 + 0.04, 0);
      pages.castShadow = true;
      group.add(pages);

      const bottomCover = new THREE.Mesh(new THREE.BoxGeometry(COVER_W, 0.08, COVER_H), plainMat);
      bottomCover.position.set(0.1, 0.04, 0);
      bottomCover.castShadow = true;
      group.add(bottomCover);

      const spine = new THREE.Mesh(new THREE.BoxGeometry(0.12, BOOK_H + 0.12, COVER_H), plainMat);
      spine.position.set(-BOOK_W / 2 - 0.01, (BOOK_H + 0.12) / 2, 0);
      group.add(spine);

      const topCoverHinge = new THREE.Group();
      topCoverHinge.position.set(-BOOK_W / 2 - 0.01, BOOK_H + 0.08, 0);

      const topCover = new THREE.Mesh(new THREE.BoxGeometry(COVER_W, 0.08, COVER_H), [
        plainMat, plainMat, coverMat, new THREE.MeshStandardMaterial({ color: 0xeadbb8 }), plainMat, plainMat
      ]);
      topCover.position.set(COVER_W / 2, 0, 0);
      topCover.castShadow = true;
      topCoverHinge.add(topCover);
      group.add(topCoverHinge);

      group.userData = { bookData: data, topCoverHinge: topCoverHinge, coverMat: coverMat, targetX: data.x, targetZ: 0 };
      
      // Kitabı masanın ÜZERİNE sıfırla (y: 0 tam alt kapak tabanıdır)
      group.position.set(data.x, 8, -4);
      group.rotation.x = -0.2;
      scene.add(group);
      bookObjects.push(group);

      new TWEEN.Tween(group.position).to({ y: 0, z: 0 }, 1200).delay(400 + index * 150).easing(TWEEN.Easing.Bounce.Out).start();
      new TWEEN.Tween(group.rotation).to({ x: 0 }, 1000).delay(400 + index * 150).easing(TWEEN.Easing.Cubic.Out).start();
    });

    new TWEEN.Tween(camera.position).to(CAMERA_REST, 2000).delay(200).easing(TWEEN.Easing.Quartic.Out).start();
    setTimeout(() => deskUi.classList.add('visible'), 1600);

    // --- SÜRÜKLE BIRAK VE HOVER FİZİĞİ ---
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    let selectedBookGroup = null;
    let hoveredBookGroup = null;
    let draggedBookGroup = null;
    let dragOffset = new THREE.Vector3();
    let isTransitioning = false;
    let isDragged = false;

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
      new TWEEN.Tween(group.position).to({ y: isHover ? 0.4 : 0 }, 300).easing(TWEEN.Easing.Quadratic.Out).start();
      new TWEEN.Tween(group.userData.topCoverHinge.rotation).to({ z: isHover ? 0.12 : 0 }, 300).easing(TWEEN.Easing.Quadratic.Out).start();
      const mat = group.userData.coverMat;
      new TWEEN.Tween(mat).to({ emissiveIntensity: isHover ? 0.4 : 0 }, 300).onUpdate(() => mat.emissive.set(0xd4af37)).start();
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
        canvas.style.cursor = 'grabbing';
        
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersect = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, intersect);
        dragOffset.copy(intersect).sub(draggedBookGroup.position);

        // Hover efektini sabitle
        new TWEEN.Tween(hit.position).to({ y: 0.6 }, 200).start();
      }
    });

    window.addEventListener('pointerup', e => {
      if (draggedBookGroup) {
        canvas.style.cursor = 'grab';
        const group = draggedBookGroup;
        draggedBookGroup = null;

        // Yere bırakma animasyonu
        new TWEEN.Tween(group.position).to({ y: 0 }, 300).easing(TWEEN.Easing.Bounce.Out).start();
        group.userData.targetX = group.position.x;
        group.userData.targetZ = group.position.z;

        // Eğer hiç sürüklenmediyse KİTABI AÇ
        if (!isDragged) {
          triggerOpenBook(group);
        }
      }
    });

    // --- STPAGEFLIP OKUYUCU MOTORU ---
    let pageFlipInstance = null;
    let currentPagesData = [];
    const flipbookEl = document.getElementById('flipbook');
    const bookContainer = document.getElementById('bookContainer');
    const pageStatusEl = document.getElementById('pageStatus');

    function buildPagesForBook(bookData) {
      const pages = [];
      const coverUrl = coverDataUrls[bookData.id];

      // 1. Dış Ön Kapak (Canvas 1:1)
      pages.push({
        density: 'hard',
        html: `<div class="cover-face" style="background-image: url('${coverUrl}'); box-shadow: none;"></div>`
      });

      // 2. İç Ön Kapak
      pages.push({
        density: 'hard',
        html: `<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#c5b592;"><div style="background:#fbf6ec; border:2px solid #d4af37; padding:24px; text-align:center; border-radius:4px;"><div style="font-family:'Cinzel',serif; font-size:13px; font-weight:700; color:#30110d;">VAKF-I KÜTÜB</div><div style="font-family:'Amiri',serif; font-size:22px; color:#7a1d1d; margin:6px 0;">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div><p style="font-size:13px; color:#4a3b2c;">${bookData.title}<br><strong>${bookData.subtitle}</strong></p></div></div>`
      });

      // KİTAP 1
      if (bookData.id === "camiur-ruhas") {
        const issues = window.FIKH_DATABASE.camiur_ruhas || [];
        pages.push({
          density: 'soft',
          html: `<div class="page-inner"><div class="running-header"><span>CÂMİU'R-RUHAS</span><span>MÜNDERECÂT</span></div><h2 class="chapter-title">Fihrist (001 - 024)</h2><ul class="toc-list" style="overflow-y:auto; max-height:540px;">` +
          issues.slice(0, 24).map((it, idx) => `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${4 + idx * 2})"><span><strong>Mesele ${it.id}:</strong> ${it.title.substring(0, 32)}...</span><span style="color:var(--gold-dim); font-weight:700;">s. ${5 + idx * 2}</span></li>`).join('') +
          `</ul><div class="running-footer"><span>Fihrist</span><span>— 1 —</span></div></div>`
        });

        pages.push({
          density: 'soft',
          html: `<div class="page-inner"><div class="running-header"><span>CÂMİU'R-RUHAS</span><span>MÜNDERECÂT II</span></div><h2 class="chapter-title">Fihrist (025 - 048)</h2><ul class="toc-list" style="overflow-y:auto; max-height:540px;">` +
          issues.slice(24, 48).map((it, idx) => `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${52 + idx * 2})"><span><strong>Mesele ${it.id}:</strong> ${it.title.substring(0, 32)}...</span><span style="color:var(--gold-dim); font-weight:700;">s. ${53 + idx * 2}</span></li>`).join('') +
          `</ul><div class="running-footer"><span>Fihrist</span><span>— 2 —</span></div></div>`
        });

        issues.forEach((it, idx) => {
          let pNum = 5 + idx * 2;
          pages.push({
            density: 'soft',
            html: `<div class="page-inner"><div class="running-header"><span>${it.chapter}</span><span>MESELE ${it.id}</span></div><div class="section-kicker">${it.chapter}</div><h2 class="chapter-title">Mesele ${it.id}: ${it.title}</h2><div class="ruhsat-banner"><span class="ruhsat-badge">LİTE TATBİKAT RUHSATI</span><div class="ruhsat-text">${it.ruhsat.hukum}</div><div style="font-size:11px; color:var(--emerald); margin-top:2px; font-weight:600;">Esas Alınan: ${it.ruhsat.mezhep}</div></div><div class="mezhep-grid"><div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Hanefî</span><span class="mezhep-tag hanefi">Hanefî</span></div><div style="font-size:12px;">${it.madhabs.hanefi.hukum}</div>${it.madhabs.hanefi.kaynak ? `<div class="arabic-quote">${it.madhabs.hanefi.kaynak.substring(0, 95)}...</div>` : ''}</div><div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Şâfiî</span><span class="mezhep-tag safii">Şâfiî</span></div><div style="font-size:12px;">${it.madhabs.safii.hukum}</div></div><div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Mâlikî</span><span class="mezhep-tag maliki">Mâlikî</span></div><div style="font-size:12px;">${it.madhabs.maliki.hukum}</div></div><div class="mezhep-card"><div class="mezhep-header"><span class="mezhep-name">Hanbelî</span><span class="mezhep-tag hanbeli">Hanbelî</span></div><div style="font-size:12px;">${it.madhabs.hanbeli.hukum}</div></div></div><div class="running-footer"><span>Câmiu'r-Ruhas</span><span>— ${pNum} —</span></div></div>`
          });
          pages.push({
            density: 'soft',
            html: `<div class="page-inner"><div class="running-header"><span>MESELE ${it.id}</span><span>TAHKÎK &amp; TELFÎK</span></div><div class="section-kicker">USÛL VE İLLET</div><h3 style="font-family:'Cormorant Garamond',serif; margin:4px 0; font-size:16.5px; color:var(--leather-outer);">Menşe-i Hilâf ve Hikmet</h3><div style="font-size:13px; text-align:justify; line-height:1.5; margin-bottom:8px;">${it.hilaf || 'Dört mezhebin delalet ve usûl kurallarına göre tahrîc edilmiştir.'}</div><div class="telfik-box"><div class="telfik-title">⚖ TELFÎK DENETİMİ VE FETVÂ GÜVENCESİ</div><div style="line-height:1.45; margin-top:2px;">${it.telfik || 'İcmâ-i mürekkep riski bulunmamaktadır.'}</div></div><div class="running-footer"><span>Tahkîk</span><span>— ${pNum + 1} —</span></div></div>`
          });
        });

        const icma = window.FIKH_DATABASE.icma || [];
        for (let i = 0; i < icma.length; i += 6) {
          const chunk = icma.slice(i, i + 6);
          pages.push({
            density: 'soft',
            html: `<div class="page-inner"><div class="running-header"><span>EL-MÜTTEFEK ALEYH</span><span>İCMÂ HÜKÜMLERİ</span></div><h2 class="chapter-title">Dört Mezhebin İttifakı (${i + 1} - ${Math.min(i + 6, icma.length)})</h2><div style="display:flex; flex-direction:column; gap:6px;">` +
            chunk.map(c => `<div style="background:rgba(255,255,255,0.6); border-left:3px solid var(--gold); padding:5px 8px; font-size:12.5px;"><strong>${c.id}. ${c.title}:</strong> ${c.rule}</div>`).join('') +
            `</div><div class="running-footer"><span>İcmâ Kanunu</span><span>— İcmâ —</span></div></div>`
          });
        }
      }

      // KİTAP 2 ve 3 (Aslî Nasslar)
      else {
        const list = bookData.id === "kitabul-asl" ? window.FIKH_DATABASE.corpus_hm : window.FIKH_DATABASE.corpus_sh;
        
        pages.push({
          density: 'soft',
          html: `<div class="page-inner"><div class="running-header"><span>${bookData.title}</span><span>MÜNDERECÂT</span></div><h2 class="chapter-title">Fihrist-i Cilt</h2><ul class="toc-list">` +
          list.slice(0, 15).map((n, idx) => `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${4 + idx})"><span>${n.eser} — ${n.kitab}</span></li>`).join('') +
          `</ul><div class="running-footer"><span>Fihrist</span><span>— 1 —</span></div></div>`
        });

        pages.push({
          density: 'soft',
          html: `<div class="page-inner"><div class="running-header"><span>${bookData.title}</span><span>MÜNDERECÂT II</span></div><h2 class="chapter-title">Fihrist (Devam)</h2><ul class="toc-list">` +
          list.slice(15, 30).map((n, idx) => `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${19 + idx})"><span>${n.eser} — ${n.kitab}</span></li>`).join('') +
          `</ul><div class="running-footer"><span>Fihrist</span><span>— 2 —</span></div></div>`
        });

        list.forEach((n, idx) => {
          pages.push({
            density: 'soft',
            html: `<div class="page-inner"><div class="running-header"><span>${n.eser}</span><span>ASIL NASS</span></div><h2 class="chapter-title">${n.muellif} — ${n.eser}</h2><div style="font-size:12px; color:var(--ink-soft); margin-bottom:4px;">Cilt: ${n.cilt} | Sayfa: ${n.sayfa} | ${n.kitab || ''}</div><div class="arabic-quote" style="font-size:15px; line-height:1.8;">« ${n.metin} »</div><div class="running-footer"><span>Klasik Külliyat</span><span>— ${idx + 3} —</span></div></div>`
          });
        });
      }

      // StPageFlip İçin Kesin Çift Sayfa Garantisi
      if (pages.length % 2 !== 0) {
        pages.push({
          density: 'soft',
          html: `<div class="page-inner" style="justify-content:center; align-items:center; text-align:center;"><div style="font-family:'Cinzel',serif; font-size:12px; color:var(--gold-dim);">BEYAZ SAHÎFE</div></div>`
        });
      }

      // Sondan Önceki İç Kapak
      pages.push({
        density: 'hard',
        html: `<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#c5b592;"><div style="background:#fbf6ec; border:2px solid #d4af37; padding:20px; text-align:center; border-radius:4px;"><div style="font-family:'Cinzel',serif; font-size:12px; font-weight:700; color:#30110d;">HÂTİME-İ CİLT</div><div class="cover-rule"></div><div style="font-size:12px; color:#4a3b2c;">Klasik Sert Cilt Mekanizması ile Ciltlenmiştir.</div></div></div>`
      });

      // Arka Kapak (Canvas 1:1)
      pages.push({
        density: 'hard',
        html: `<div class="cover-face" style="background-image: url('${coverUrl}'); box-shadow: none;"></div>`
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
      
      // Senkron DOM Üretimi
      let htmlString = "";
      currentPagesData.forEach(p => {
        htmlString += `<div class="page" data-density="${p.density}">${p.html}</div>`;
      });
      flipbookEl.innerHTML = htmlString;

      const targetW = 470;
      const targetH = 680;

      // DOM'un render olması için çok kısa bir an bekle
      setTimeout(() => {
        pageFlipInstance = new St.PageFlip(flipbookEl, {
          width: targetW, height: targetH, size: 'stretch',
          minWidth: 280, maxWidth: 1200, minHeight: 380, maxHeight: 1400,
          showCover: true, maxShadowOpacity: 0.55, usePortrait: false,
          drawShadow: true, flippingTime: 750, startPage: 0
        });

        const renderedPages = document.querySelectorAll('#flipbook .page');
        pageFlipInstance.loadFromHTML(renderedPages);
        pageFlipInstance.on('flip', e => updateReaderUi(e.data));
        
        bookContainer.style.transition = 'none';
        updateReaderUi(0);
        void bookContainer.offsetHeight;
        bookContainer.style.transition = '';
      }, 10);
    }

    function triggerOpenBook(group) {
      if (isTransitioning) return;
      isTransitioning = true;
      selectedBookGroup = group;
      deskUi.classList.add('hidden');
      const data = group.userData.bookData;

      prepareReader(data);

      new TWEEN.Tween(group.position).to({ x: 0, y: 5.5, z: 6.5 }, 850).easing(TWEEN.Easing.Cubic.InOut).start();
      new TWEEN.Tween(group.rotation).to({ x: 0.95, y: 0, z: 0 }, 850).easing(TWEEN.Easing.Cubic.InOut)
        .onComplete(() => {
          group.visible = false;
          readerScreen.classList.add('screen-active');
          isTransitioning = false;
          setTimeout(() => {
            if (pageFlipInstance) pageFlipInstance.flipNext('bottom');
            
            // STEAM BAŞARIMI (Sadece ilk açılışta)
            if (!achievementUnlocked) {
              achievementUnlocked = true;
              setTimeout(() => {
                achievementToast.classList.add('show');
                setTimeout(() => achievementToast.classList.remove('show'), 4000);
              }, 800);
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
      currentZoom = Math.min(1.5, currentZoom + 0.1);
      document.documentElement.style.setProperty('--zoom-factor', currentZoom);
      document.getElementById('zoomDisplay').textContent = Math.round(currentZoom * 100) + '%';
    });
    document.getElementById('zoomOutBtn').addEventListener('click', () => {
      currentZoom = Math.max(0.7, currentZoom - 0.1);
      document.documentElement.style.setProperty('--zoom-factor', currentZoom);
      document.getElementById('zoomDisplay').textContent = Math.round(currentZoom * 100) + '%';
    });

    let currentFontSize = 14.5;
    document.getElementById('fontIncBtn').addEventListener('click', () => {
      currentFontSize = Math.min(19, currentFontSize + 1);
      document.documentElement.style.setProperty('--book-font-size', currentFontSize + 'px');
    });
    document.getElementById('fontDecBtn').addEventListener('click', () => {
      currentFontSize = Math.max(12, currentFontSize - 1);
      document.documentElement.style.setProperty('--book-font-size', currentFontSize + 'px');
    });

    // --- EVRENSEL ARAMA SİSTEMİ ---
    const searchInput = document.getElementById('searchInput');
    const tocModal = document.getElementById('tocModal');
    const modalTocList = document.getElementById('modalTocList');

    searchInput.addEventListener('input', e => {
      const q = e.target.value.toLowerCase().trim();
      if (q.length < 2) return;
      
      const issueResults = (window.FIKH_DATABASE.camiur_ruhas || []).filter(it => 
        it.title.toLowerCase().includes(q) || 
        it.ruhsat.hukum.toLowerCase().includes(q) ||
        it.chapter.toLowerCase().includes(q)
      );

      const hmResults = (window.FIKH_DATABASE.corpus_hm || []).filter(n =>
        n.metin.toLowerCase().includes(q) || (n.bab && n.bab.toLowerCase().includes(q))
      );

      const shResults = (window.FIKH_DATABASE.corpus_sh || []).filter(n =>
        n.metin.toLowerCase().includes(q) || (n.bab && n.bab.toLowerCase().includes(q))
      );

      let resHtml = `<div style="padding-bottom:6px; font-weight:700; color:var(--ruby);">${issueResults.length + hmResults.length + shResults.length} Arama Sonucu Bulundu:</div><ul class="toc-list">`;
      
      if (issueResults.length > 0) {
        resHtml += `<li style="padding:6px 0 2px; font-weight:700; color:var(--gold-dim);">[1. KİTAP: CÂMİU'R-RUHAS]</li>`;
        issueResults.slice(0, 15).forEach(r => {
          resHtml += `<li class="toc-item" onclick="openBookIssue('camiur-ruhas', ${r.id})"><span><strong>Mesele ${r.id}:</strong> ${r.title}</span><span style="color:var(--emerald); font-size:12px;">${r.ruhsat.mezhep}</span></li>`;
        });
      }

      if (hmResults.length > 0) {
        resHtml += `<li style="padding:8px 0 2px; font-weight:700; color:var(--gold-dim);">[2. KİTAP: EL-ASL &amp; EL-KÂFÎ (HANEFÎ/MÂLİKÎ)]</li>`;
        hmResults.slice(0, 8).forEach(n => {
          resHtml += `<li class="toc-item" onclick="openClassicalBook('kitabul-asl')"><span><strong>[${n.mezhep}] ${n.muellif} — ${n.eser}</strong></span><div class="arabic-quote" style="font-size:13px;">${n.metin.substring(0, 120)}...</div></li>`;
        });
      }

      if (shResults.length > 0) {
        resHtml += `<li style="padding:8px 0 2px; font-weight:700; color:var(--gold-dim);">[3. KİTAP: EL-ÜMM &amp; EL-MUĞNÎ (ŞÂFİÎ/HANBELÎ)]</li>`;
        shResults.slice(0, 8).forEach(n => {
          resHtml += `<li class="toc-item" onclick="openClassicalBook('kitabul-umm')"><span><strong>[${n.mezhep}] ${n.muellif} — ${n.eser}</strong></span><div class="arabic-quote" style="font-size:13px;">${n.metin.substring(0, 120)}...</div></li>`;
        });
      }

      resHtml += '</ul>';
      modalTocList.innerHTML = resHtml;
      document.getElementById('modalTitle').textContent = "EVRENSEL KÜTÜPHANE ARAMASI";
      tocModal.classList.add('active');
    });

    window.openBookIssue = function(bookId, issueId) {
      tocModal.classList.remove('active');
      let targetGroup = bookObjects.find(g => g.userData.bookData.id === bookId);
      if (!targetGroup) return;

      if (!selectedBookGroup || selectedBookGroup.userData.bookData.id !== bookId) {
        triggerOpenBook(targetGroup);
      }
      setTimeout(() => {
        let targetPage = 4 + (issueId - 1) * 2;
        if (pageFlipInstance) pageFlipInstance.turnToPage(targetPage);
      }, 900);
    };

    window.openClassicalBook = function(bookId) {
      tocModal.classList.remove('active');
      let targetGroup = bookObjects.find(g => g.userData.bookData.id === bookId);
      if (!targetGroup) return;
      if (!selectedBookGroup || selectedBookGroup.userData.bookData.id !== bookId) {
        triggerOpenBook(targetGroup);
      }
    };

    document.getElementById('openCorpusBtn').addEventListener('click', () => {
      const hmList = window.FIKH_DATABASE.corpus_hm || [];
      const shList = window.FIKH_DATABASE.corpus_sh || [];
      let html = `<div style="padding-bottom:8px; font-weight:700; color:var(--ruby);">KORPUSTAN DERLENEN ASLÎ ARAPÇA NASSLAR:</div><ul class="toc-list">`;
      [...hmList.slice(0, 20), ...shList.slice(0, 20)].forEach(n => {
        html += `<li class="toc-item" style="background:rgba(212,175,55,0.05); margin-bottom:6px; border-left:3px solid var(--gold); padding:6px 10px;"><span><strong>[${n.mezhep}] ${n.muellif} — ${n.eser} (C:${n.cilt}, S:${n.sayfa})</strong></span><div style="font-size:12px; color:var(--ink-soft);">${n.kitab || ''} - ${n.bab || ''}</div><div class="arabic-quote" style="font-size:13.5px; margin-top:4px;">${n.metin}</div></li>`;
      });
      html += '</ul>';
      modalTocList.innerHTML = html;
      document.getElementById('modalTitle').textContent = "HAM NASSLAR VE KLASİK FIKIH METİNLERİ";
      tocModal.classList.add('active');
    });

    document.getElementById('openTocBtn').addEventListener('click', () => {
      if (!selectedBookGroup) return;
      const bData = selectedBookGroup.userData.bookData;
      let html = '<ul class="toc-list">';
      if (bData.id === "camiur-ruhas") {
        const issues = window.FIKH_DATABASE.camiur_ruhas || [];
        issues.slice(0, 100).forEach((it, idx) => {
          let pNum = 4 + idx * 2;
          html += `<li class="toc-item" onclick="pageFlipInstance.turnToPage(${pNum}); tocModal.classList.remove('active');"><span><strong>Mesele ${it.id}:</strong> ${it.title}</span><span style="color:var(--gold-dim); font-weight:700;">s. ${pNum+1}</span></li>`;
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
      camera.lookAt(CAMERA_LOOK.x, CAMERA_LOOK.y, CAMERA_LOOK.z);
      renderer.render(scene, camera);
    }
    animate();
  </script>
</body>
</html>'''

    full_output = HTML_HEAD + json_data + HTML_TAIL

    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(full_output)

    size_mb = os.path.getsize(OUTPUT_HTML_PATH) / (1024 * 1024)
    print("=" * 80)
    print(f"[✓] TAM TEŞEKKÜLLÜ STANDALONE KÜLLİYAT ÜRETİLDİ: {OUTPUT_HTML_PATH}")
    print(f"    Sürükle-Bırak Fiziği Aktif, Page-Flip Sorunu Giderildi.")
    print("=" * 80)

if __name__ == "__main__":
    generate_web_library()
