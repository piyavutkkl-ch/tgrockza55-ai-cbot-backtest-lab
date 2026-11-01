with open('docs/research.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Remove premature calls
c = c.replace("            filterStrategies();\n        renderEmbeddedChat();", "            filterStrategies();")
c = c.replace("        filterStrategies();\n        renderEmbeddedChat();", "        filterStrategies();")

# 2. Add renderEmbeddedChat call inside switchTab
c = c.replace(
    "          content.classList.remove('hidden');",
    "          content.classList.remove('hidden');\n          if (t === 'timeline' && typeof renderEmbeddedChat === 'function') { renderEmbeddedChat(); }"
)

# 3. Add direct call at end of embedded chat script
old_script_end = """    function handleEmbeddedChatSearch() {
      const inp = document.getElementById('chatSearchInput');
      embeddedChatSearch = inp ? inp.value : '';
      renderEmbeddedChat();
    }
  </script>"""

new_script_end = """    function handleEmbeddedChatSearch() {
      const inp = document.getElementById('chatSearchInput');
      embeddedChatSearch = inp ? inp.value : '';
      renderEmbeddedChat();
    }

    // Auto-run embedded chat render on load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderEmbeddedChat);
    } else {
      renderEmbeddedChat();
    }
  </script>"""

assert old_script_end in c, "old_script_end not found"
c = c.replace(old_script_end, new_script_end)

with open('docs/research.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("docs/research.html script call order fixed!")
