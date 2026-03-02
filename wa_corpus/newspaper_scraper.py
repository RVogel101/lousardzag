"""
Western Armenian newspaper scraper — multi-source.

Scrapes Armenian-language articles from accessible WA news sources:
  - Aztag Daily (aztagdaily.com) — Beirut-based WA daily
  - Horizon Weekly (horizonweekly.ca) — Montreal-based WA weekly

Uses Selenium for JavaScript-rendered pages.
Rate-limited to be respectful of servers.

Usage:
    python -m wa_corpus.newspaper_scraper [--max-pages N] [--output-dir DIR]
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR = Path("wa_corpus/data/newspapers")
REQUEST_DELAY = 2.0


# ─── Source Definitions ──────────────────────────────────────────────

class NewsSource:
    """Configuration for a single newspaper source."""

    def __init__(
        self,
        name: str,
        base_url: str,
        listing_url: str,
        pagination_pattern: str,
        article_link_selector: str,
        article_body_selector: str,
        title_selector: str = "h1",
        date_selector: str = "time",
        max_listing_pages: int = 50,
    ):
        self.name = name
        self.base_url = base_url
        self.listing_url = listing_url
        self.pagination_pattern = pagination_pattern
        self.article_link_selector = article_link_selector
        self.article_body_selector = article_body_selector
        self.title_selector = title_selector
        self.date_selector = date_selector
        self.max_listing_pages = max_listing_pages


AZTAG = NewsSource(
    name="aztag",
    base_url="https://www.aztagdaily.com",
    listing_url="https://www.aztagdaily.com/archives/category/featured",
    pagination_pattern="https://www.aztagdaily.com/archives/category/featured/page/{page}",
    article_link_selector="h2 a, .entry-title a, article a[href*='/archives/']",
    article_body_selector=".entry-content, .post-content, article .content",
    title_selector="h1.entry-title, h1",
    date_selector="time, .entry-date, .post-date",
)

HORIZON = NewsSource(
    name="horizon",
    base_url="https://horizonweekly.ca",
    listing_url="https://horizonweekly.ca/hy/category/armenian/",
    pagination_pattern="https://horizonweekly.ca/hy/category/armenian/page/{page}/",
    article_link_selector=(
        "h2.entry-title a, h3.entry-title a, .td-module-title a, "
        ".entry-title a, h2 a, article a[href*='horizonweekly.ca']"
    ),
    article_body_selector=".entry-content, .td-post-content, .post-content",
    title_selector="h1.entry-title, h1.tdb-title-text, h1",
    date_selector="time, .entry-date, .td-post-date, .td-post-meta-date",
)

ASBAREZ = NewsSource(
    name="asbarez",
    base_url="https://asbarez.com",
    listing_url="https://asbarez.com/category/armenian/",
    pagination_pattern="https://asbarez.com/category/armenian/page/{page}/",
    article_link_selector=(
        "h2.entry-title a, h3.entry-title a, .entry-title a, "
        "h2 a, article a[href*='asbarez.com']"
    ),
    article_body_selector=".entry-content, .post-content, article .content",
    title_selector="h1.entry-title, h1",
    date_selector="time, .entry-date, .post-date",
)

ALL_SOURCES = [AZTAG, HORIZON, ASBAREZ]


# ─── Browser Setup ───────────────────────────────────────────────────

def _create_driver() -> webdriver.Chrome:
    """Create a headless Chrome driver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


# ─── Helpers ─────────────────────────────────────────────────────────

def _has_armenian(text: str, min_chars: int = 10) -> bool:
    """Check if text contains substantial Armenian content."""
    arm_count = sum(1 for c in text if 0x0531 <= ord(c) <= 0x0587)
    return arm_count >= min_chars


def _extract_armenian_links(driver: webdriver.Chrome, selector: str, base_url: str) -> list[str]:
    """Extract article URLs that likely contain Armenian content."""
    urls: list[str] = []
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for elem in elements:
            href = elem.get_attribute("href") or ""
            text = elem.text.strip()
            # Accept links that have Armenian text or are article-like URLs
            if href and href.startswith(base_url):
                # Strip fragment (#respond, etc.) to avoid duplicates
                href = href.split("#")[0]
                if _has_armenian(text, min_chars=5) or re.search(r"/archives/\d+", href):
                    if href not in urls:
                        urls.append(href)
    except Exception:
        pass
    return urls


# ─── Article Collection ──────────────────────────────────────────────

def collect_article_urls(
    driver: webdriver.Chrome,
    source: NewsSource,
    max_pages: int | None = None,
) -> list[str]:
    """Collect article URLs from listing pages."""
    max_pages = max_pages or source.max_listing_pages
    all_urls: list[str] = []
    seen: set[str] = set()

    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            url = source.listing_url
        else:
            url = source.pagination_pattern.format(page=page_num)

        logger.info("[%s] Listing page %d: %s", source.name, page_num, url)

        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Let dynamic content render
        except Exception:
            logger.warning("[%s] Could not load listing page %d", source.name, page_num)
            break

        # Check if page has content (not 404)
        if "404" in driver.title or len(driver.page_source) < 500:
            logger.info("[%s] Page %d appears empty/404, stopping", source.name, page_num)
            break

        links = _extract_armenian_links(driver, source.article_link_selector, source.base_url)

        new_count = 0
        for link in links:
            if link not in seen:
                seen.add(link)
                all_urls.append(link)
                new_count += 1

        logger.info("[%s]   Found %d new links (total: %d)", source.name, new_count, len(all_urls))

        if new_count == 0:
            logger.info("[%s]   No new links, stopping pagination", source.name)
            break

        time.sleep(REQUEST_DELAY)

    return all_urls


# ─── Article Extraction ─────────────────────────────────────────────

def extract_article(
    driver: webdriver.Chrome,
    url: str,
    source: NewsSource,
) -> dict | None:
    """Extract article text from a single page."""
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1)
    except Exception:
        logger.warning("[%s] Failed to load: %s", source.name, url)
        return None

    # Title
    title = ""
    try:
        for sel in source.title_selector.split(", "):
            elems = driver.find_elements(By.CSS_SELECTOR, sel.strip())
            if elems:
                title = elems[0].text.strip()
                break
    except Exception:
        pass

    # Date
    date_str = ""
    try:
        for sel in source.date_selector.split(", "):
            elems = driver.find_elements(By.CSS_SELECTOR, sel.strip())
            if elems:
                date_str = elems[0].get_attribute("datetime") or elems[0].text.strip()
                break
    except Exception:
        pass

    # Body — try each selector
    body = ""
    for sel in source.article_body_selector.split(", "):
        try:
            content_elems = driver.find_elements(By.CSS_SELECTOR, sel.strip())
            if content_elems:
                paragraphs = content_elems[0].find_elements(By.TAG_NAME, "p")
                body = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
                if body:
                    break
        except Exception:
            continue

    if not body:
        # Fallback: try all <p> tags in the page
        try:
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            armenian_p = [p.text.strip() for p in paragraphs
                          if p.text.strip() and _has_armenian(p.text, 10)]
            body = "\n".join(armenian_p)
        except Exception:
            pass

    if not body or not _has_armenian(body, 30):
        return None

    return {
        "source": source.name,
        "url": url,
        "title": title,
        "date": date_str,
        "text": body,
    }


# ─── Checkpoint / Resume ─────────────────────────────────────────────

def _load_checkpoint(output_dir: Path) -> tuple[set[str], list[dict]]:
    """Load previously scraped articles."""
    checkpoint_file = output_dir / "articles.jsonl"
    scraped_urls: set[str] = set()
    articles: list[dict] = []

    if checkpoint_file.exists():
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    article = json.loads(line)
                    scraped_urls.add(article["url"])
                    articles.append(article)
        logger.info("Loaded %d previously scraped articles", len(articles))

    return scraped_urls, articles


def _save_article(output_dir: Path, article: dict) -> None:
    """Append a single article to checkpoint."""
    checkpoint_file = output_dir / "articles.jsonl"
    with open(checkpoint_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(article, ensure_ascii=False) + "\n")


# ─── Main Pipeline ───────────────────────────────────────────────────

def scrape_newspapers(
    max_listing_pages: int = 50,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    sources: list[NewsSource] | None = None,
) -> list[dict]:
    """Scrape all configured newspaper sources.

    Returns list of article dicts.
    """
    sources = sources or ALL_SOURCES
    output_dir.mkdir(parents=True, exist_ok=True)
    scraped_urls, articles = _load_checkpoint(output_dir)

    driver = _create_driver()
    try:
        for source in sources:
            logger.info("=" * 50)
            logger.info("  Scraping: %s (%s)", source.name, source.base_url)
            logger.info("=" * 50)

            # Collect URLs
            all_urls = collect_article_urls(driver, source, max_listing_pages)
            new_urls = [u for u in all_urls if u not in scraped_urls]
            logger.info("[%s] %d new articles to scrape (of %d found)",
                        source.name, len(new_urls), len(all_urls))

            # Scrape articles
            for i, url in enumerate(new_urls, 1):
                logger.info("[%s] [%d/%d] %s", source.name, i, len(new_urls), url)
                article = extract_article(driver, url, source)

                if article:
                    articles.append(article)
                    _save_article(output_dir, article)
                    scraped_urls.add(url)
                    logger.info("[%s]   OK: %d chars", source.name, len(article["text"]))
                else:
                    logger.info("[%s]   Skipped (no Armenian content)", source.name)

                time.sleep(REQUEST_DELAY)

    finally:
        driver.quit()

    logger.info("Scraping complete: %d total articles across all sources", len(articles))
    return articles


def load_newspaper_texts(output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[str]:
    """Load previously scraped article texts."""
    _, articles = _load_checkpoint(output_dir)
    return [a["text"] for a in articles if a.get("text")]


# ─── CLI ──────────────────────────────────────────────────────────────

def main():
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Scrape WA newspaper articles")
    parser.add_argument("--max-pages", type=int, default=50,
                        help="Max listing pages per source")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source", choices=["aztag", "horizon", "all"], default="all",
                        help="Which source to scrape")
    args = parser.parse_args()

    if args.source == "aztag":
        sources = [AZTAG]
    elif args.source == "horizon":
        sources = [HORIZON]
    else:
        sources = ALL_SOURCES

    articles = scrape_newspapers(args.max_pages, args.output_dir, sources)

    from .tokenizer import count_frequencies, filter_by_min_length

    texts = [a["text"] for a in articles]
    freq = count_frequencies(texts)
    freq = filter_by_min_length(freq, min_len=2)

    print(f"\nArticles: {len(articles)}")
    print(f"Tokens:   {sum(freq.values()):,}")
    print(f"Types:    {len(freq):,}")


if __name__ == "__main__":
    main()
