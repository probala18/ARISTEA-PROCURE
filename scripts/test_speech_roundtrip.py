import urllib.request
import json
import base64
import time

BASE = 'http://localhost:8000'

def test_speech():
    print("1. Synthesizing audio...")
    synth_req = urllib.request.Request(
        f'{BASE}/api/speech/synthesize',
        data=json.dumps({'text': 'flexible cables for home wiring', 'language': 'en'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(synth_req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        audio_b64 = res['audio_base64']
        audio_bytes = base64.b64decode(audio_b64)
        print(f"Synthesized audio size: {len(audio_bytes)} bytes")

    print("\n2. Transcribing synthesized audio...")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="speech.mp3"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode("utf-8") + audio_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    trans_req = urllib.request.Request(
        f"{BASE}/api/speech/transcribe?language_hint=en",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(trans_req) as resp:
            trans_res = json.loads(resp.read().decode('utf-8'))
            print(f"Transcription status: {resp.status} (Time: {time.time()-t0:.3f}s)")
            print(json.dumps(trans_res, indent=2))
    except Exception as e:
        print(f"Transcription failed: {e}")

if __name__ == "__main__":
    test_speech()
