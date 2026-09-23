import urllib.request
import json
import time

BASE = "http://localhost:8000"

def test_async():
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    content = b"Section 1: General Requirements\r\n1.1 Supply cables conforming to IS 694:2010.\r\n"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="async_tender.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE}/api/jobs/tenders/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        sub = json.loads(resp.read().decode("utf-8"))
        print(f"Submitted async job: {json.dumps(sub, indent=2)}")
        job_id = sub["id"]

    for i in range(10):
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE}/api/jobs/{job_id}") as resp:
            st = json.loads(resp.read().decode("utf-8"))
            print(f"Poll #{i+1}: status={st['status']}, progress={st.get('progress')}")
            if st["status"] in ["COMPLETED", "FAILED"]:
                print("Job finished!")
                break

if __name__ == "__main__":
    test_async()
