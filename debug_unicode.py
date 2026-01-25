
import sys
import unicodedata
from pathlib import Path

# Mock tomllib
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("No toml lib found")
        sys.exit(1)

def check():
    rules_path = Path("app/config/rules.toml")
    if not rules_path.exists():
        # Try full path if CWD is wrong
        rules_path = Path("/home/kalmerg/eeel/kuts2/app/config/rules.toml")
    
    with open(rules_path, 'rb') as f:
        data = tomllib.load(f)

    # Find ehitusjuht_tase_6
    q = next((q for q in data['qualifications'] if q['id'] == 'ehitusjuht_tase_6'), None)
    if not q:
        print("Qualification not found")
        return

    # Find ej6_deg_matched_300
    p = next((p for p in q['eligibility_packages'] if p['id'] == 'ej6_deg_matched_300'), None)
    if not p:
        print("Package not found")
        return

    toml_val = p['education_requirement']
    py_val = "vastav_kõrgharidus_300_eap"

    print(f"TOML value: {toml_val!r}")
    print(f"Py value:   {py_val!r}")
    
    if toml_val == py_val:
        print("Strings match perfectly.")
    else:
        print("Strings DO NOT match.")
        if unicodedata.normalize('NFC', toml_val) == unicodedata.normalize('NFC', py_val):
            print("Strings match after NFC normalization.")
        else:
            print("Strings do not match even after normalization.")

if __name__ == "__main__":
    check()
