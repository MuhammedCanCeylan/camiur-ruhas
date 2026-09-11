import os
import re
import sqlite3
from tqdm import tqdm

DB_PATH = os.path.join("metadata", "fikh_corpus.db")

print("=" * 80)
print("[*] FAZ 2.3: FIKIH BILGI GRAFI (KNOWLEDGE GRAPH) MOTORU BASLATILDI")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS graph_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT,
    mezhep TEXT,
    eser TEXT,
    entity_type TEXT,
    entity_val TEXT,
    raw_snippet TEXT,
    FOREIGN KEY(node_id) REFERENCES fikh_nodes(node_id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS graph_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT,
    mezhep TEXT,
    hukum TEXT,
    delil_turu TEXT,
    illet_snippet TEXT,
    FOREIGN KEY(node_id) REFERENCES fikh_nodes(node_id)
);
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_ent_node ON graph_entities(node_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_ent_type ON graph_entities(entity_type);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_mezhep ON graph_relations(mezhep);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_hukum ON graph_relations(hukum);")

cursor.execute("DELETE FROM graph_entities;")
cursor.execute("DELETE FROM graph_relations;")
conn.commit()

HUKUM_PATTERNS = {
    "Farz_Vacip": [r"\b(فرض|واجب|يفترض|يجب|أوجب|الوجوب|فريضته)\b"],
    "Sunnet_Mustehap": [r"\b(سنة|مستحب|يندب|مندوب|مسنون|سنتها|استحب)\b"],
    "Haram": [r"\b(يحرم|حرام|محرم|حرمة|لا يحل|لا يجوز بحال)\b"],
    "Mekruh": [r"\b(يكره|مكروه|كراهة|كره)\b"],
    "Caiz_Mubah": [r"\b(يجوز|جائز|يباح|مباح|الجواز|لا بأس|أجزأ|يجزئ)\b"],
    "Batil_Fasit": [r"\b(يبطل|باطل|يفسد|فاسد|بطلان|فساد|لا يجزئ|لا صحة)\b"],
    "Sart_Rukun": [r"\b(شرط|ركن|شروط|أركان|مشروط)\b"]
}

DELIL_PATTERNS = {
    "Ayet": [r"(قال الله تعالى|لقوله تعالى|قوله عز وجل|في التنزيل|لقول الله|قوله سبحانه)"],
    "Hadis": [r"(صلى الله عليه وسلم|روى|عن النبي|في الخبر|لقوله عليه الصلاة والسلام|حديث|أثر)"],
    "Icma": [r"(أجمعوا|الإجماع|إجماع|لا خلاف بينهم|اتفقوا|إجماعا)"],
    "Kiyas": [r"(قياساً|قياسا على|لأنه يشبه|أشبه|والأصل فيه القياس)"],
    "Istihsan": [r"(استحساناً|استحسانا|وجه الاستحسان|والقياس كذا والاستحسان)"],
    "Amel_i_Medine": [r"(عمل أهل المدينة|الأمر عندنا بمكة|الأمر المجمع عليه عندنا)"]
}

ILLET_PATTERNS = [
    r"(?:والعلة في ذلك|لأنه|ولأنها|باعتبار أنه|والمعنى فيه|بجامع|لكونه|علة ذلك)\s+([^.\n]{15,120})"
]

cursor.execute("SELECT node_id, mezhep, eser, metin_orijinal FROM fikh_nodes;")
nodes = cursor.fetchall()

entity_inserts = []
relation_inserts = []

for nid, mezhep, eser, metin in tqdm(nodes, desc="Graf Çıkarımı", unit="node"):
    detected_hukums = set()
    detected_delils = set()
    detected_illets = []

    for hukum_type, patterns in HUKUM_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, metin)
            if m:
                detected_hukums.add(hukum_type)
                start = max(0, m.start() - 25)
                end = min(len(metin), m.end() + 25)
                entity_inserts.append((nid, mezhep, eser, "HUKUM", hukum_type, metin[start:end]))
                break

    for delil_type, patterns in DELIL_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, metin)
            if m:
                detected_delils.add(delil_type)
                start = max(0, m.start() - 20)
                end = min(len(metin), m.end() + 45)
                entity_inserts.append((nid, mezhep, eser, "DELIL", delil_type, metin[start:end]))
                break

    for pat in ILLET_PATTERNS:
        matches = re.findall(pat, metin)
        for ill in matches:
            clean_ill = ill.strip()
            if len(clean_ill) > 15:
                detected_illets.append(clean_ill)
                entity_inserts.append((nid, mezhep, eser, "ILLET", "Gerekce", clean_ill))

    if detected_hukums and detected_delils:
        primary_illet = detected_illets[0] if detected_illets else ""
        for h in detected_hukums:
            for d in detected_delils:
                relation_inserts.append((nid, mezhep, h, d, primary_illet))

    if len(entity_inserts) >= 50000:
        cursor.executemany("INSERT INTO graph_entities (node_id, mezhep, eser, entity_type, entity_val, raw_snippet) VALUES (?, ?, ?, ?, ?, ?);", entity_inserts)
        entity_inserts = []

    if len(relation_inserts) >= 50000:
        cursor.executemany("INSERT INTO graph_relations (node_id, mezhep, hukum, delil_turu, illet_snippet) VALUES (?, ?, ?, ?, ?);", relation_inserts)
        relation_inserts = []

if entity_inserts:
    cursor.executemany("INSERT INTO graph_entities (node_id, mezhep, eser, entity_type, entity_val, raw_snippet) VALUES (?, ?, ?, ?, ?, ?);", entity_inserts)

if relation_inserts:
    cursor.executemany("INSERT INTO graph_relations (node_id, mezhep, hukum, delil_turu, illet_snippet) VALUES (?, ?, ?, ?, ?);", relation_inserts)

conn.commit()

cursor.execute("SELECT COUNT(*) FROM graph_entities;")
total_ent = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM graph_relations;")
total_rel = cursor.fetchone()[0]

print("\n" + "=" * 80)
print("BILGI GRAFI ENVENTER RAPORU:")
print(f"  - Çıkarılan Varlık (Entity) : {total_ent:,}")
print(f"  - Kurulan İlişki (Relation) : {total_rel:,}")
print("=" * 80)

conn.close()
