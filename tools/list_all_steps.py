import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript_full.jsonl"

all_steps = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        t = data.get('type')
        c = data.get('content', '')
        ts = data.get('created_at', '')
        step_idx = data.get('step_index')
        if t in ['USER_INPUT', 'PLANNER_RESPONSE']:
            all_steps.append({
                'step_index': step_idx,
                'type': t,
                'time': ts,
                'has_content': bool(c),
                'content_preview': (c[:60] if c else '').replace('\n', ' ')
            })

print(f"Total steps with USER_INPUT or PLANNER_RESPONSE: {len(all_steps)}")
for s in all_steps:
    print(f"Step {s['step_index']}: {s['type']} | Content: {s['has_content']} | {s['content_preview']}")
