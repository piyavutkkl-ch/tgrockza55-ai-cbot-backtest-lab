import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\cbot-atgvt\research\chatgpt_script_8.js', 'r', encoding='utf-8') as f:
    content = f.read()

# In React Router / Remix stream, it might be an array of serialized objects, or we can extract JSON payload
match = re.search(r'window\.__reactRouterContext\.streamController\.enqueue\((.*)\)', content, re.DOTALL)
if match:
    json_str = match.group(1).strip()
    if json_str.endswith(');'):
        json_str = json_str[:-2]
    elif json_str.endswith(')'):
        json_str = json_str[:-1]
    
    # Sometimes it's a JSON-encoded string that decodes to array
    try:
        parsed = json.loads(json_str)
        # If parsed is string, decode again
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        print(f"Parsed type: {type(parsed)}, length: {len(parsed) if hasattr(parsed, '__len__') else 'N/A'}")
        
        # Save parsed
        with open(r'd:\cbot-atgvt\research\chatgpt_parsed_stream.json', 'w', encoding='utf-8') as pf:
            json.dump(parsed, pf, ensure_ascii=False, indent=2)
        print("Saved to chatgpt_parsed_stream.json")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        # Let's inspect snippet
        print("Snippet:", json_str[:300])
