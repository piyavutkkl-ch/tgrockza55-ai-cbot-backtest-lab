import subprocess
import json

with open('docs/chat_transcript.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<script id="chat-data" type="application/json">') + len('<script id="chat-data" type="application/json">')
end = text.find('</script>', start)
data = json.loads(text[start:end].strip())

last_msg = data[-1]
print("Last message text length:", len(last_msg['text']))
print("Contains 14 modules table:", "Winning Method Per Module" in last_msg['text'])
print("Contains Microstructure Insights:", "Core Microstructure Insights" in last_msg['text'])
print("Contains Code Files:", "ไฟล์โค้ดและข้อมูลผลการทดสอบ" in last_msg['text'])
