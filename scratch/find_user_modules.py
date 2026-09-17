import json

transcript_path = r"C:\Users\BALASUNDAR M\.gemini\antigravity-ide\brain\19bbda88-3e1f-40ff-bd7a-7039d747026c\.system_generated\logs\transcript.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        if data.get("type") == "USER_INPUT":
            content = data.get("content", "")
            first_line = content.splitlines()[0] if content else ""
            print(f"Step {data.get('step_index')}: {first_line[:80]}")
            if "Module" in content or "MODULE" in content:
                for l in content.splitlines():
                    if "Module" in l or "MODULE" in l:
                        print(f"   -> {l[:100]}")
