import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript_full.jsonl"

last_user = ""
last_assistant = ""

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            last_user = data.get('content', '')
        elif data.get('type') == 'PLANNER_RESPONSE' and data.get('content'):
            last_assistant = data.get('content', '')

print("=== LAST USER ===")
print(last_user)
print("\n=== LAST ASSISTANT ===")
print(last_assistant)
