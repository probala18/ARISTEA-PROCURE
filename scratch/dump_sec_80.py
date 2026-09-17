import json

transcript_path = r"C:\Users\BALASUNDAR M\.gemini\antigravity-ide\brain\19bbda88-3e1f-40ff-bd7a-7039d747026c\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
    data = json.loads(first_line)
    content = data.get("content", "")

lines = content.splitlines()

with open("scratch/model_strategy_section_80.txt", "w", encoding="utf-8") as out:
    for i in range(2405, 2445):
        out.write(f"[{i}] {lines[i]}\n")

print("Dumped section 80")
