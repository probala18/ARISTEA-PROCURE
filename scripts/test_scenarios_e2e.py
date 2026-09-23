import urllib.request
import urllib.error
import json
import time

BASE = "http://localhost:8000"

def post_json(name, url, payload):
    t0 = time.time()
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            elapsed = time.time() - t0
            body = resp.read().decode("utf-8")
            print(f"=== {name} (Time: {elapsed:.3f}s) ===")
            print(f"Status: {resp.status}")
            res = json.loads(body)
            print(json.dumps(res, indent=2)[:600] + "...\n")
            return res
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        err_body = e.read().decode("utf-8")
        print(f"=== {name} HTTPError {e.code} (Time: {elapsed:.3f}s) ===")
        print(err_body[:500] + "\n")
        return None
    except Exception as e:
        elapsed = time.time() - t0
        print(f"=== {name} FAILED (Time: {elapsed:.3f}s) ===: {e}\n")
        return None

# Test Tender Audit with sample text tender
tender_payload = {
    "tender_text": "Supply and installation of 2.5 sq mm PVC insulated copper flexible cables conforming to IS 694 for domestic electrical wiring. All cables must have ISI mark.",
    "title": "Demo / Test Document - Electrical Cabling Tender"
}
audit_res = post_json("Tender Audit", f"{BASE}/api/tenders/audit", tender_payload)

# Test Specification Generation
spec_payload = {
    "standard_id": "IS 694:2010",
    "specification_type": "technical_specification",
    "tender_context": "Supply of PVC insulated flexible copper cables for residential lighting circuits",
    "parameters": {
        "voltage_grade": "450/750 V",
        "conductor": "Copper"
    }
}
spec_res = post_json("Specification Generation", f"{BASE}/api/specifications/generate", spec_payload)

# Test Speech Synthesize
speech_synth_payload = {
    "text": "Welcome to ARISTEA PROCURE demo",
    "language": "en"
}
synth_res = post_json("Speech Synthesize", f"{BASE}/api/speech/synthesize", speech_synth_payload)
