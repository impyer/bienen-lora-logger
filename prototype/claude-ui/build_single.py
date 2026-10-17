#!/usr/bin/env python3
"""Build the portable, one-file Bienenlogger preview from the canonical sources.

Do not put a live <script> in <head>: inline scripts execute immediately even
if "defer" is set, and our app requires DOM nodes in <body>.
"""
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('--dir', type=Path, default=Path(__file__).parent)
p.add_argument('--output', type=Path)
a = p.parse_args()
source_dir = a.dir
html = (source_dir / 'index.html').read_text(encoding='utf-8')
css = (source_dir / 'style.css').read_text(encoding='utf-8')
js = (source_dir / 'app.js').read_text(encoding='utf-8')
live = (source_dir / 'stockkarte_live.js').read_text(encoding='utf-8')
editor = (source_dir / 'stockkarte_edit.js').read_text(encoding='utf-8')
native = (source_dir / 'stockkarte_native.js').read_text(encoding='utf-8')
assert html.count('<link rel="stylesheet" href="style.css">') == 1
assert html.count('<script defer src="app.js"></script>') == 1
assert html.count('<script defer src="stockkarte_live.js"></script>') == 1
assert html.count('<script defer src="stockkarte_edit.js"></script>') == 1
assert html.count('<script defer src="stockkarte_native.js"></script>') == 1
assert html.count('</body>') == 1
# Inline CSS remains in head. JavaScript must be at the END OF BODY.
html = html.replace('<link rel="stylesheet" href="style.css">',
                    '  <style>\n' + css.replace('</style', '<\\/style') + '\n  </style>')
html = html.replace('<script defer src="stockkarte_native.js"></script>', '')
html = html.replace('<script defer src="app.js"></script>', '')
html = html.replace('<script defer src="stockkarte_live.js"></script>', '')
html = html.replace('<script defer src="stockkarte_edit.js"></script>', '')
html = html.replace('</body>', '  <script>\n' + native.replace('</script', '<\\/script') + '\n  </script>\n  <script>\n' + js.replace('</script', '<\\/script') + '\n  </script>\n  <script>\n' + live.replace('</script', '<\\/script') + '\n  </script>\n  <script>\n' + editor.replace('</script', '<\\/script') + '\n  </script>\n</body>')
output = a.output or source_dir / 'bienenlogger-claude-prototyp.html'
output.write_text(html, encoding='utf-8')
print('Created:', output, '('+str(output.stat().st_size)+' bytes)')
