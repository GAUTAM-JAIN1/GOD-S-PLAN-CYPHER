with open("backend/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "def list_domains" in l:
        print("".join(lines[i:i+35]))
        break
