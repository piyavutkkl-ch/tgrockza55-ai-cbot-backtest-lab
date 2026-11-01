import os
import sys
import json
import html

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Strong Baesus PC1\.gemini\antigravity\brain\066c0b89-502c-4b32-b8ff-2f8201902c09\.system_generated\logs\transcript_full.jsonl"
out_html_path = r"d:\cbot-atgvt\zz_zz PAPER\web\chat_transcript.html"

messages = []
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                data = json.loads(line)
                step_type = data.get('type')
                source = data.get('source')
                content = data.get('content', '')
                created_at = data.get('created_at', '')
                
                if step_type == 'USER_INPUT':
                    # Filter out system tags like <CONTEXT_SUMMARY> or similar if needed
                    text = content
                    if '<CONTEXT_SUMMARY>' in text:
                        # Extract the actual user query at the top if present
                        pass
                    messages.append({
                        'role': 'user',
                        'time': created_at,
                        'text': text
                    })
                elif step_type == 'PLANNER_RESPONSE' and content:
                    messages.append({
                        'role': 'assistant',
                        'time': created_at,
                        'text': content
                    })
            except Exception as e:
                continue

print(f"Parsed {len(messages)} messages from transcript.")

# Render to beautiful modern HTML
html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Antigravity Chat Transcript - 141 Quant Strategies & Backtest Lab</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root {{
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent: #38bdf8;
    --user-bubble: #1e3a8a;
    --bot-bubble: #1e293b;
    --border: #334155;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    padding: 24px;
  }}
  .container {{
    max-width: 1000px;
    margin: 0 auto;
  }}
  header {{
    text-align: center;
    padding: 24px 0 32px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
  }}
  h1 {{ font-size: 24px; color: var(--accent); margin-bottom: 8px; }}
  .subtitle {{ color: var(--text-secondary); font-size: 14px; }}
  .chat-stream {{ display: flex; flex-direction: column; gap: 24px; }}
  .message {{
    display: flex;
    flex-direction: column;
    padding: 18px 22px;
    border-radius: 12px;
    border: 1px solid var(--border);
  }}
  .message.user {{
    background-color: #1e2d4a;
    border-color: #3b82f6;
    align-self: flex-end;
    max-width: 85%;
  }}
  .message.assistant {{
    background-color: var(--bot-bubble);
    border-color: var(--border);
    align-self: flex-start;
    width: 100%;
  }}
  .meta {{
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    font-weight: bold;
  }}
  .content {{
    font-size: 15px;
    overflow-x: auto;
  }}
  .content p {{ margin-bottom: 12px; }}
  .content table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 13px;
  }}
  .content th, .content td {{
    border: 1px solid var(--border);
    padding: 8px 12px;
    text-align: left;
  }}
  .content th {{ background-color: #334155; color: #38bdf8; }}
  .content pre {{
    background: #090d16;
    padding: 14px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 14px 0;
    border: 1px solid #1e293b;
    font-family: Consolas, monospace;
    font-size: 13px;
  }}
  .content code {{
    background: #334155;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
  }}
  .content pre code {{ background: none; padding: 0; }}
  .content a {{ color: #38bdf8; text-decoration: none; }}
  .content a:hover {{ text-decoration: underline; }}
  .badge {{
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    text-transform: uppercase;
  }}
  .badge.user {{ background: #2563eb; color: #fff; }}
  .badge.assistant {{ background: #0284c7; color: #fff; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>💬 บทสนทนาการวิจัยควอนต์ & cBot Backtest Lab</h1>
    <div class="subtitle">Antigravity AI Pair Programming Session | การค้นคว้า 141 งานวิจัย & ระบบ 13-Engine Quant Benchmark</div>
  </header>
  <div class="chat-stream" id="chatStream">
"""

for msg in messages:
    role = msg['role']
    time_str = msg['time'][:19].replace('T', ' ') if msg['time'] else ''
    badge_label = "USER (ผู้ใช้งาน)" if role == 'user' else "ANTIGRAVITY (AI QUANT)"
    badge_class = "user" if role == 'user' else "assistant"
    
    # Escape raw markdown string safely into JS string
    raw_text_json = json.dumps(msg['text'], ensure_ascii=False)
    
    html_content += f"""
    <div class="message {role}">
      <div class="meta">
        <span class="badge {badge_class}">{badge_label}</span>
        <span>{time_str}</span>
      </div>
      <div class="content" data-markdown={html.escape(raw_text_json)}></div>
    </div>
"""

html_content += """
  </div>
</div>
<script>
  document.querySelectorAll('.content[data-markdown]').forEach(el => {
    try {
      const raw = JSON.parse(el.getAttribute('data-markdown'));
      el.innerHTML = marked.parse(raw);
    } catch(e) {
      el.textContent = el.getAttribute('data-markdown');
    }
  });
</script>
</body>
</html>
"""

os.makedirs(os.path.dirname(out_html_path), exist_ok=True)
with open(out_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Exported chat HTML to: {out_html_path}")
