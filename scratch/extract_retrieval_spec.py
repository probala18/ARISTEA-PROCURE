import json

transcript_path = r"C:\Users\BALASUNDAR M\.gemini\antigravity-ide\brain\19bbda88-3e1f-40ff-bd7a-7039d747026c\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
    data = json.loads(first_line)
    content = data.get("content", "")

lines = content.splitlines()

matches = []
for idx, line in enumerate(lines):
    l_lower = line.lower()
    if any(k in l_lower for k in ["semantic retrieval", "embedding provider", "vector indexing", "lexical retrieval", "hybrid retrieval", "hybrid scoring", "reciprocal rank", "bm25", "embeddings"]):
        matches.append(idx)

with open("scratch/retrieval_spec_dump.txt", "w", encoding="utf-8") as out:
    out.write(f"Found {len(matches)} matching line locations.\n")
    for m in matches:
        out.write(f"--- Line {m} ---\n")
        start = max(0, m - 5)
        end = min(len(lines), m + 35)
        for j in range(start, end):
            out.write(f"[{j}] {lines[j]}\n")

print(f"Dumped {len(matches)} matches to scratch/retrieval_spec_dump.txt")
