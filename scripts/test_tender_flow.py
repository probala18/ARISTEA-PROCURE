import urllib.request
import urllib.parse
import json
import time

BASE = "http://localhost:8000"

def test_tender_flow():
    # 1. Upload tender
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = "test_tender.txt"
    content = b"""PROCUREMENT OF LOW VOLTAGE ELECTRICAL CABLES
Section 1: General Requirements
1.1 The contractor shall supply and install PVC insulated flexible copper conductor cables.
1.2 All electrical cables shall conform to IS 694:2010.
1.3 Testing shall adhere to applicable Indian Standards including IS 8130:2013 for conductors.
1.4 The cables shall carry BIS certification and ISI mark.
"""
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE}/api/tenders/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    t0 = time.time()
    with urllib.request.urlopen(req) as resp:
        upload_res = json.loads(resp.read().decode("utf-8"))
        print(f"=== Tender Upload (Time: {time.time()-t0:.3f}s) ===")
        print(f"Status: {resp.status}")
        print(json.dumps(upload_res, indent=2))
        tender_id = upload_res["tender_id"]

    # 2. Get requirements
    req = urllib.request.Request(f"{BASE}/api/tenders/{tender_id}/requirements")
    with urllib.request.urlopen(req) as resp:
        reqs_res = json.loads(resp.read().decode("utf-8"))
        print(f"\n=== Tender Requirements ===")
        print(f"Total: {reqs_res['total_requirements']}")

    # 3. Get references
    req = urllib.request.Request(f"{BASE}/api/tenders/{tender_id}/references")
    with urllib.request.urlopen(req) as resp:
        refs_res = json.loads(resp.read().decode("utf-8"))
        print(f"\n=== Tender References ===")
        print(f"Total: {refs_res['total_references']}")
        for ref in refs_res.get("references", []):
            print(f" - Raw: {ref['standard_number_raw']}, Valid: {ref['is_valid']}, Detected: {ref['detected_standard_id']}")

    # 4. Get audit
    t0 = time.time()
    req = urllib.request.Request(f"{BASE}/api/tenders/{tender_id}/audit")
    with urllib.request.urlopen(req) as resp:
        audit_res = json.loads(resp.read().decode("utf-8"))
        print(f"\n=== Tender Audit (Time: {time.time()-t0:.3f}s) ===")
        print(f"Coverage Score: {audit_res.get('coverage_score')}")
        print(f"Coverage Percentage: {audit_res.get('coverage_percentage')}%")
        print(f"Present Standards: {len(audit_res.get('present_standards', []))}")
        print(f"Gaps: {len(audit_res.get('gaps', []))}")
        print(f"Trust Disclaimer: {audit_res.get('trust_disclaimer', '')[:80]}...")

if __name__ == "__main__":
    test_tender_flow()
