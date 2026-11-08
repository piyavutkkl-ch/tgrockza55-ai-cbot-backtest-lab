import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\cbot-atgvt\research\chatgpt_parsed_stream.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total elements: {len(data)}")

# Find all string elements
strings = [x for x in data if isinstance(x, str)]
print(f"Total string elements: {len(strings)}")

# Look for Thai strings or long strings
long_strings = [s for s in strings if len(s) > 100]
print(f"Strings > 100 chars: {len(long_strings)}")

thai_strings = [s for s in strings if any('\u0e00' <= c <= '\u0e7f' for c in s)]
print(f"Thai strings: {len(thai_strings)}")

with open(r'd:\cbot-atgvt\research\chatgpt_extracted_messages.txt', 'w', encoding='utf-8') as out_f:
    for i, s in enumerate(thai_strings):
        out_f.write(f"\n--- THAI STRING {i} (len {len(s)}) ---\n")
        out_f.write(s + "\n")

    out_f.write("\n=================== LONG STRINGS (TOP 30) ===================\n")
    for i, s in enumerate(sorted(long_strings, key=len, reverse=True)[:30]):
        out_f.write(f"\n--- LONG STRING {i} (len {len(s)}) ---\n")
        out_f.write(s[:2000] + "\n")

print("Saved extracted messages to d:\cbot-atgvt\research\chatgpt_extracted_messages.txt")
