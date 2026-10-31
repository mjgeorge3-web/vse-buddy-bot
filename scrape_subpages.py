"""Script to scrape subpages of InSIS: Course catalog, Final theses, Academic schedule, Help."""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin
import json

urls_to_scrape = {
    "theses": "https://insis.vse.cz/zp/?lang=en",
    "courses": "https://insis.vse.cz/katalog/?lang=en",
    "schedule": "https://insis.vse.cz/student/harmonogram.pl?lang=en",
    "financing": "https://insis.vse.cz/financovani/index.pl?lang=en",
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

class TextAndLinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_chunks = []
        self.links = []
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == "a":
            attrs_dict = dict(attrs)
            if "href" in attrs_dict:
                self.links.append(attrs_dict["href"])

    def handle_data(self, data):
        clean = data.strip()
        if clean and len(clean) > 2 and self.current_tag not in ["script", "style"]:
            self.text_chunks.append(clean)

subpage_data = {}

for key, url in urls_to_scrape.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            parser = TextAndLinkExtractor()
            parser.feed(html)
            subpage_data[key] = {
                "url": url,
                "text_sample": parser.text_chunks[:25],
                "links_count": len(parser.links),
            }
            print(f"Scraped {key}: {len(html)} bytes, {len(parser.text_chunks)} text fragments, {len(parser.links)} links")
            print("  Top text:", " | ".join(parser.text_chunks[:6]))
    except Exception as e:
        print(f"Error scraping {key} ({url}): {e}")

with open("insis_subpages_scraped.json", "w", encoding="utf-8") as f:
    json.dump(subpage_data, f, indent=2, ensure_ascii=False)

print("Saved subpage analysis to insis_subpages_scraped.json")
