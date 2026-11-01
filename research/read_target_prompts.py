import json
import sys

p = r'C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript.jsonl'
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        obj = json.loads(line)
        if obj.get('source') == 'USER_EXPLICIT' or obj.get('type') == 'USER_INPUT':
            content = obj.get('content', '')
            # clean up tag
            c_text = content.replace('<USER_REQUEST>', '').replace('</USER_REQUEST>', '').strip()
            print(f"[{i}] {c_text[:300]}")
