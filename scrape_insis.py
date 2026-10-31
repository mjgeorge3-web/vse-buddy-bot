"""Script to scrape and analyze the structure, links, portals, and menus of insis.vse.cz using standard library."""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import urllib.request
import re
import json
from html.parser import HTMLParser
from urllib.parse import urljoin

base_url = "https://insis.vse.cz/?lang=en"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_a = None
        self.text_buf = []
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "a":
            attrs_dict = dict(attrs)
            if "href" in attrs_dict:
                self.current_a = attrs_dict["href"]
                self.text_buf = []

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "a":
            if self.current_a:
                text = "".join(self.text_buf).strip()
                if text and not self.current_a.startswith("javascript"):
                    full_url = urljoin(base_url, self.current_a)
                    self.links.append({"text": text, "href": self.current_a, "full_url": full_url})
                self.current_a = None
                self.text_buf = []

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.current_a is not None:
            self.text_buf.append(data)

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

html = fetch(base_url)
print(f"Fetched {len(html)} bytes from {base_url}")

parser = LinkParser()
parser.feed(html)

print("Page Title:", parser.title.strip())
print(f"Total extracted links: {len(parser.links)}")

print("\n--- Key Menu Items / Portals Found on InSIS Homepage ---")
for item in parser.links[:50]:
    print(f" - {item['text']} -> {item['href']}")

# Save extracted structure as JSON
with open("insis_scraped_structure.json", "w", encoding="utf-8") as f:
    json.dump({"url": base_url, "title": parser.title.strip(), "links": parser.links}, f, indent=2, ensure_ascii=False)

print("\nSaved structure to insis_scraped_structure.json")
