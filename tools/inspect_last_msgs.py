import json

with open('docs/chat_transcript.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<script id="chat-data" type="application/json">') + len('<script id="chat-data" type="application/json">')
end = text.find('</script>', start)
data = json.loads(text[start:end].strip())

print(f"Total messages: {len(data)}")
for m in data[-4:]:
    print(f"\n--- ID #{m['id']} [{m['role']}] ({m['time']}) (len {len(m['text'])}) ---")
    print(m['text'][:250])
    print("...")
    print(m['text'][-200:])
