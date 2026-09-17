import json

transcript_path = r"C:\Users\BALASUNDAR M\.gemini\antigravity-ide\brain\19bbda88-3e1f-40ff-bd7a-7039d747026c\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
    data = json.loads(first_line)
    content = data.get("content", "")

lines = content.splitlines()

with open("scratch/retrieval_sections_26_to_29.txt", "w", encoding="utf-8") as out:
    for i in range(930, 1070):
        out.write(f"[{i}] {lines[i]}\n")

with open("scratch/retrieval_sections_74_to_75.txt", "w", encoding="utf-8") as out:
    for i in range(2235, 2290):
        out.write(f"[{i}] {lines[i]}\n")

print("Dumped sections 26-29 and 74-75")
