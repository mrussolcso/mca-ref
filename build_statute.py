import sys
import re
import urllib.request
from bs4 import BeautifulSoup

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def parse_mca_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    # Remove navigation, headers, and footers
    for elem in soup(['nav', 'header', 'footer', 'script', 'style']):
        elem.decompose()

    # Extract Title/Statute Header
    title_text = "Montana Code Annotated"
    for h in soup.find_all(['h1', 'h2', 'h3']):
        txt = clean_text(h.get_text())
        if re.search(r'\d+-\d+-\d+', txt) or "CHAPTER" in txt or "Part" in txt:
            title_text = txt
            break

    # Extract Legal Body Lines
    lines = []
    # Targeted containers commonly used on leg.mt.gov
    main_content = soup.find('main') or soup.find('body')
    
    raw_paragraphs = main_content.find_all(['p', 'div']) if main_content else []
    for p in raw_paragraphs:
        txt = clean_text(p.get_text())
        if txt and not txt.startswith("TITLE") and not txt.startswith("CHAPTER"):
            lines.append(txt)

    # Convert lines into structured CSS Grid items
    formatted_items = []
    history_text = ""

    for line in lines:
        if line.startswith("History:"):
            history_text = line
            continue

        # Regex match for hierarchy: (1), (a), (i), (A), or (6)(a)
        match = re.match(r'^(\(\d+\)(?:\s*\([a-z]\))?|\([a-z]\)|\([i|v|x]+\)|\([A-Z]\))\s*(.*)', line)
        if match:
            counter, content = match.groups()
            level_class = "level-num"
            if re.match(r'^\([a-z]\)', counter):
                level_class = "level-alpha"
            elif re.match(r'^\([i|v|x]+\)', counter):
                level_class = "level-roman"
            elif re.match(r'^\([A-Z]\)', counter):
                level_class = "level-cap-alpha"

            formatted_items.append(
                f'<li class="{level_class}"><span class="counter">{counter}</span><div>{content}</div></li>'
            )
        else:
            if len(line) > 10:  # Skip tiny stray fragments
                formatted_items.append(f'<li class="level-num"><div>{line}</div></li>')

    list_html = "\n".join(formatted_items)
    
    return title_text, list_html, history_text

def build_card_html(title, list_html, history_text, source_url):
    # Extract statute number for bond lookup (e.g., 45-5-502)
    statute_num_match = re.search(r'\d+-\d+-\d+', title)
    statute_num = statute_num_match.group(0) if statute_num_match else "MCA Section"

    return f"""
  <!-- {statute_num} CARD -->
  <div class="statute-card">
    <div class="statute-header">{title}</div>
    
    <!-- Bond Book Summary Bar -->
    <div class="bond-info-grid">
      <div class="bond-stat"><span class="label">Offense Degree</span><span class="value">Misd. / Felony</span></div>
      <div class="bond-stat"><span class="label">Recommended Bond</span><span class="value">See Bond Schedule</span></div>
      <div class="bond-stat"><span class="label">Must Appear?</span><span class="value must-appear">REQUIRED</span></div>
      <div class="bond-stat"><span class="label">Source</span><span class="value"><a href="{source_url}" target="_blank">MCA Source</a></span></div>
    </div>

    <!-- Collapsible Full Text -->
    <details class="statute-accordion" open>
      <summary class="accordion-trigger">Full Statutory Text (Click to Collapse/Expand)</summary>
      <div class="statute-body">
        <ol class="statute-list">
          {list_html}
        </ol>
        <div class="history-text">{history_text}</div>
      </div>
    </details>
  </div>
"""

def update_index_page(card_html):
    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Montana Code Annotated & Bond Reference</title>
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
  .bond-stat .value a {{ color: var(--primary); text-decoration: underline; }}
  .bond-stat .value.must-appear {{ color: var(--accent-red); }}

  /* Collapsible Accordion */
  details.statute-accordion {{ border-top: 1px solid var(--border); }}
  summary.accordion-trigger {{ padding: 14px 20px; font-weight: 700; color: var(--primary); background: #f7fafc; cursor: pointer; user-select: none; border-bottom: 1px solid var(--border); }}
  summary.accordion-trigger:hover {{ background: #edf2f7; }}
  
  /* CSS Grid Layout for Hanging Indents */
  .statute-body {{ padding: 20px 24px; }}
  .statute-list {{ list-style: none; padding-left: 0; margin: 0; }}
  .statute-list li {{ display: grid; grid-template-columns: auto 1fr; column-gap: 8px; margin-bottom: 10px; line-height: 1.6; }}
  .counter {{ font-weight: 700; color: var(--primary); white-space: nowrap; }}
  
  .level-num {{ margin-left: 0px; }}
  .level-alpha {{ margin-left: 24px; }}
  .level-roman {{ margin-left: 48px; }}
  .level-cap-alpha {{ margin-left: 72px; }}

  .history-text {{ margin-top: 20px; padding-top: 12px; font-size: 0.85rem; color: #718096; border-top: 1px dashed var(--border); font-style: italic; }}
</style>
</head>
<body>
<div class="container">
{card_html}
</div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(template)

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://mca.legmt.gov/bills/mca/title_0450/chapter_0050/part_0050/section_0020/0450-0050-0050-0020.html"
    title, list_html, history_text = parse_mca_url(target_url)
    card_html = build_card_html(title, list_html, history_text, target_url)
    update_index_page(card_html)
