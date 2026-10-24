#!/usr/bin/env python3
"""Generate the root sitemap and robots.txt for xylin48.site.

Only non-empty, public HTML pages are listed. index.html maps to the site root.
The lastmod value comes from the page's latest Git commit, not the build time.
"""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from subprocess import run
from urllib.parse import quote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://xylin48.site"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", SITEMAP_NS)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "template", "noscript"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "template", "noscript"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth and data.strip():
            self.parts.append(data.strip())


def has_visible_content(path):
    parser = VisibleText()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return False
    return bool(" ".join(parser.parts).strip())


def last_modified(relative_path):
    result = run(
        ["git", "log", "-1", "--format=%cs", "--", relative_path.as_posix()],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    value = result.stdout.strip()
    if value:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    return None


def main():
    urlset = ET.Element(f"{{{SITEMAP_NS}}}urlset")
    pages = []
    for path in sorted(ROOT.rglob("*.html")):
        relative = path.relative_to(ROOT)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if relative.name.startswith("google") and "verification" in relative.name:
            continue
        if not has_visible_content(path):
            continue
        if relative.as_posix() == "index.html":
            url = BASE_URL + "/"
        else:
            url = BASE_URL + "/" + quote(relative.as_posix(), safe="/-._~")
        pages.append((url, relative))

    for url, relative in pages:
        item = ET.SubElement(urlset, f"{{{SITEMAP_NS}}}url")
        ET.SubElement(item, f"{{{SITEMAP_NS}}}loc").text = url
        modified = last_modified(relative)
        if modified:
            ET.SubElement(item, f"{{{SITEMAP_NS}}}lastmod").text = modified

    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)

    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    print(f"Generated sitemap.xml with {len(pages)} public HTML page(s).")


if __name__ == "__main__":
    main()
