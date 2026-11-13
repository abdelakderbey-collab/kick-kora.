from pathlib import Path
import subprocess
base = Path(__file__).resolve().parent
temp = base / "PASTE_SPORTAPI_KEY_HERE.txt"
if not temp.exists():
    temp.write_text("PASTE YOUR NEW SPORTAPI KEY ON THIS LINE\n", encoding="utf-8")
subprocess.Popen(["notepad.exe", str(temp)])
print("Notepad opened. Replace the example line with your NEW SportAPI key.")
print("Save with Ctrl+S, close Notepad, then return here.")
input("Press Enter after saving and closing Notepad...")
lines = temp.read_text(encoding="utf-8-sig").splitlines()
key = next((x.strip() for x in lines if x.strip() and "PASTE YOUR NEW" not in x), "")
if not key or not key.startswith("sk_live_") or any(ch.isspace() for ch in key):
    raise SystemExit("No valid SportAPI key found. Run setup again with a new key.")
(base / ".env").write_text("SPORTAPI_KEY=" + key + "\nPORT=3000\n", encoding="utf-8")
temp.unlink(missing_ok=True)
print("SportAPI key saved locally. Run START_KICK_KORA.bat now.")
