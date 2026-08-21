#!/usr/bin/env python3
"""Dependency-free checks for the publicly deployed static site."""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = "https://www.5gserralheria.com.br"
HTML_FILES = sorted(ROOT.rglob("*.html"))
ERRORS: list[str] = []


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.robots: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", "") or "")


def error(message: str) -> None:
    ERRORS.append(message)


def page_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def local_target(source: Path, href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or href.startswith("//") or href.startswith("#"):
        return None
    pathname = unquote(parsed.path)
    if not pathname:
        return None
    candidate = ROOT / pathname.lstrip("/") if pathname.startswith("/") else source.parent / pathname
    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.suffix:
        return candidate
    return candidate / "index.html"


def validate_sitemap() -> None:
    try:
        tree = ET.parse(ROOT / "sitemap.xml")
    except ET.ParseError as exc:
        error(f"sitemap.xml is not valid XML: {exc}")
        return
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = tree.findall(".//sm:loc", namespace)
    if not locations:
        error("sitemap.xml has no <loc> entries")
    for location in locations:
        url = (location.text or "").strip()
        if not url.startswith(f"{DOMAIN}/"):
            error(f"sitemap URL does not use the official domain: {url}")


def validate_pages() -> None:
    for page in HTML_FILES:
        text = page.read_text(encoding="utf-8")
        relative = page_path(page)
        if "ayamdigital.com.br" in text:
            error(f"provisional domain found in {relative}")
        parser = PageParser()
        parser.feed(text)
        if relative != "404.html" and any("noindex" in item.lower() for item in parser.robots):
            error(f"indexable page has noindex: {relative}")
        for href in parser.links:
            target = local_target(page, href)
            if target is not None and not target.exists():
                error(f"broken internal link in {relative}: {href} -> {target.relative_to(ROOT)}")
        json_ld: list[object] = []
        for block in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S):
            try:
                json_ld.append(json.loads(block.strip()))
            except json.JSONDecodeError as exc:
                error(f"invalid JSON-LD in {relative}: {exc.msg}")
        visible_text = re.sub(r"<[^>]+>", " ", text)
        visible_text = " ".join(visible_text.split())
        for item in json_ld:
            if not isinstance(item, dict) or item.get("@type") != "FAQPage":
                continue
            for question in item.get("mainEntity", []):
                if not isinstance(question, dict):
                    continue
                answer = question.get("acceptedAnswer", {})
                question_text = question.get("name", "")
                answer_text = answer.get("text", "") if isinstance(answer, dict) else ""
                if question_text and question_text not in visible_text:
                    error(f"FAQPage question is not visible in {relative}: {question_text}")
                if answer_text and answer_text not in visible_text:
                    error(f"FAQPage answer is not visible in {relative}: {question_text}")


def main() -> int:
    validate_sitemap()
    validate_pages()
    if ERRORS:
        print("Validation failed:")
        print("\n".join(f"- {item}" for item in ERRORS))
        return 1
    print(f"Validated {len(HTML_FILES)} HTML pages, sitemap XML, URLs, links and JSON-LD.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
