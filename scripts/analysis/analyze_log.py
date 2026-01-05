
file_path = "logs/success_verification.txt"
try:
    with open(file_path, "r", encoding="utf-16") as f:
        lines = f.readlines()
        
    print(f"Total lines: {len(lines)}")
    for i, line in enumerate(lines):
        if "ERROR" in line or "validation error" in line:
            print(f"[{i}] {line.strip()}")
except Exception as e:
    print(f"Failed to read log: {e}")
