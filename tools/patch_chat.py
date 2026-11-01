import re

with open('docs/chat_transcript.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'(\s*if \(window\.location\.hash === \'#bottom\'\) \{\s*window\.scrollTo\(0, document\.body\.scrollHeight\);\s*\})+', '', c)
c = c.replace("setTimeout(() => {\n          const target = document.querySelector(window.location.hash);\n          if (target) target.scrollIntoView({ behavior: 'smooth' });\n        }, 200);",
              "const target = document.querySelector(window.location.hash);\n        if (target) target.scrollIntoView();")

with open('docs/chat_transcript.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Cleaned up chat_transcript.html")
