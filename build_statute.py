import sys
import re
import urllib.request
from bs4 import BeautifulSoup

def fetch_and_format(url):
    # Fetch webpage via urllib
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    # Extract title/statute header
    title_el = soup.find(['h1', 'h2', 'title'])
    header_text = title_el.get_text(strip=True) if title_el else "Statute Reference"

    # Extract raw text paragraphs
    paragraphs = [p.get_text(strip=True) for p in soup.find_all(['p', 'div']) if p.get_text(strip=True)]
    
    formatted_items = []
    for line in paragraphs:
        # Categorize indentation based on Montana statutory numbering hierarchy
        if re.match(r'^\(\d+\)', line):
            formatted_items.append(f'<li class="level-num">{line}</li>')
        elif re.match(r'^\([a-z]\)', line):
            formatted_items.append(f'<li class="level-alpha">{line}</li>')
        elif re.match(r'^\([i|v|x]+\)', line):
            formatted_items.append(f'<li class="level-roman">{line}</li>')
        elif re.match(r'^\([A-Z]\)', line):
            formatted_items.append(f'<li class="level-cap-alpha">{line}</li>')

    list_content = "\n".join(formatted_items) if formatted_items else "<li>Statute text parsed directly from source.</li>"

    # HTML Card Template with Bond Summary + Collapsible Full Text
    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{header_text}</title>
<style>
  :root {{ --primary: #1a365d; --border: #e2e8f0; --text: #2d3748; --accent-red: #9b2c2c; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; color: var(--text); }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .statute-card {{ background: #fff; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 24px; overflow: hidden; }}
  .statute-header {{ background: var(--primary); color: #fff; padding: 16px 20px; font-size: 1.25rem; font-weight: 700; }}
  
  /* Bond Book Summary Bar */
  .bond-info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; background: #ebf8ff; border-bottom: 1px solid var(--border); padding: 16px 20px; }}
  .bond-stat {{ display: flex; flex-direction: column; }}
  .bond-stat .label {{ font-size: 0.75rem; text-transform: uppercase; color: #4a5568; font-weight: 600; }}
  .bond-stat .value {{ font-size: 1.05rem; font-weight: 700; color: var(--primary); }}
  .bond-stat .value.must-appear {{ color: var(--accent-red); }}

  /* Collapsible Accordion Styles */
  details.statute-accordion {{ border-top: 1px solid var(--border); }}
  summary.accordion-trigger {{ padding: 16px 20px; font-weight: 700; color: var(--primary); background: #f7fafc; cursor: pointer; user-select: none; border-bottom: 1px solid var(--border); }}
  summary.accordion-trigger:hover {{ background: #edf2f7; }}
  
  .statute-body {{ padding: 20px 24px; }}
  .statute-list {{ list-style: none; padding-left: 0; margin: 0; }}
  .statute-list li {{ margin-bottom: 10px; line-height: 1.6; }}
  .level-num {{ margin-left: 0px; font-weight: 600; }}
  .level-alpha {{ margin-left: 24px; }}
  .level-roman {{ margin-left: 48px; }}
  .level-cap-alpha {{ margin-left: 72px; }}
</style>
</head>
<body>
<div class="container">
  <div class="statute-card">
    <div class="statute-header">{header_text}</div>
    
    <!-- Bond Summary -->
    <div class="bond-info-grid">
      <div class="bond-stat"><span class="label">Offense Degree</span><span class="value">Pending Review</span></div>
      <div class="bond-stat"><span class="label">Recommended Bond</span><span class="value">See Schedule</span></div>
      <div class="bond-stat"><span class="label">Must Appear?</span><span class="value must-appear">REQUIRED</span></div>
      <div class="bond-stat"><span class="label">Source URL</span><span class="value"><a href="{url}" target="_blank" style="font-size:0.85rem;">MCA Link</a></span></div>
    </div>

    <!-- Collapsible Full Text -->
    <details class="statute-accordion" open>
      <summary class="accordion-trigger">Full Statutory Text (Click to Collapse/Expand)</summary>
      <div class="statute-body">
        <ul class="statute-list">
          {list_content}
        </ul>
      </div>
    </details>
  </div>
</div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(template)

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://leg.mt.gov/"
    fetch_and_format(target_url)
