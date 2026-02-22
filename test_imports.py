"""Quick import smoke-test — run with: python3 test_imports.py"""
import sys
sys.path.insert(0, ".")

ok = True

def check(name, fn):
    global ok
    try:
        fn()
        print(f"  ✅ {name}")
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        ok = False

print("Import chain tests:")

check("RAG.py", lambda: __import__("RAG"))
check("prompts.py", lambda: __import__("prompts"))
check("tools.py", lambda: __import__("tools"))

import yaml
def check_config():
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    assert cfg["rag"]["default_collection"] == "linear_algebra_notes"
check("config.yaml", check_config)

def check_ambient():
    from ambient import _read_manifest, WATCH_DIR
    m = _read_manifest()
    assert "LinearAlgebraNotes.pdf" in m, f"Manifest missing pre-seeded PDF: {m}"
check("ambient.py + manifest", check_ambient)

def check_collections():
    from RAG import list_collections
    cols = list_collections()
    print(f"       ChromaDB collections: {cols}")
check("RAG.list_collections()", check_collections)

print()
if ok:
    print("All checks passed! ✅")
else:
    print("Some checks failed ❌")
    sys.exit(1)
