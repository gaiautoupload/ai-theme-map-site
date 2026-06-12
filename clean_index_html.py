with open('d:/ai-theme-map-site/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's search for the duplicate block
target = """                container.appendChild(section);
            });ne-clamp-2">${map.title}</h4>"""

if target in content:
    print("Found exact target (LF).")
elif target.replace('\n', '\r\n') in content:
    print("Found exact target (CRLF).")
    target = target.replace('\n', '\r\n')
else:
    print("Target not found directly.")

# Let's look for:
# container.appendChild(section);
#             });ne-clamp-2">${map.title}</h4>
# ... up to ...
#                 container.appendChild(section);
#             });
# and replace it with:
# container.appendChild(section);
#             });
#         }

import re
# We want to match:
# container.appendChild(section); \r?\n \s* \}\);ne-clamp-2.*?container.appendChild\(section\);\s*\r?\n\s*\}\);
pattern = r'(container\.appendChild\(section\);\s*\r?\n\s*\}\);ne-clamp-2.*?\n\s*container\.appendChild\(section\);\s*\r?\n\s*\}\);)'
match = re.search(pattern, content, re.DOTALL)
if match:
    print("Regex match found!")
    matched_text = match.group(1)
    # Replace matched text with empty string or close function
    content = content.replace(matched_text, "container.appendChild(section);\n            });\n        }")
    with open('d:/ai-theme-map-site/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully cleaned index.html.")
else:
    print("Regex match not found.")
