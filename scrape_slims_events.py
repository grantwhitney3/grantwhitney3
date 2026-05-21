#!/usr/bin/env python3
"""Scrape Slim's Dive Bar events into a CSV file.

The events page uses JavaScript pagination, so this script drives a headless
browser, clicks the Modern Events Calendar "Load More" button until it is
exhausted, and then extracts the event cards that are present in the DOM.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_URL = "https://slimsdivebar.com/music-and-events/"
EVENT_SELECTOR = "#mec_skin_486 article.mec-event-article"
LOAD_MORE_SELECTOR = "#mec_skin_486 .mec-load-more-button"


def clean_text(value: str | None) -> str:
    """Normalize browser text content for CSV output."""
    return re.sub(r"\s+", " ", value or "").strip()


def detect_chrome() -> str | None:
    """Prefer an already installed Chrome/Chromium before Playwright browsers."""
    for executable in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        path = shutil.which(executable)
        if path:
            return path
    return None


def parse_event_date(date_label: str, month_heading: str) -> str:
    """Return an ISO date when the calendar's date and month heading allow it."""
    year_match = re.search(r"\b(\d{4})\b", month_heading)
    if not year_match:
        return clean_text(f"{date_label} {month_heading}")

    date_with_year = f"{date_label} {year_match.group(1)}"
    for fmt in ("%d %b %Y", "%d %B %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(date_with_year, fmt).date().isoformat()
        except ValueError:
            pass
    return clean_text(date_with_year)


def build_time_range(start_time: str, end_time: str) -> str:
    if start_time and end_time:
        return f"{start_time} - {end_time}"
    return start_time or end_time


def event_has_drink_specials(*values: str) -> str:
    haystack = " ".join(values).lower()
    return "yes" if "drink special" in haystack else "no"


def click_all_load_more(page: Any, max_clicks: int) -> None:
    """Click the scoped events load-more button until it disappears or stalls."""
    for _ in range(max_clicks):
        button = page.locator(LOAD_MORE_SELECTOR).first
        try:
            if not button.is_visible(timeout=1_000):
                return
        except PlaywrightTimeoutError:
            return

        previous_count = page.locator(EVENT_SELECTOR).count()
        button.scroll_into_view_if_needed(timeout=5_000)
        button.click(timeout=10_000)

        try:
            page.wait_for_function(
                """([eventSelector, buttonSelector, previousCount]) => {
                    const eventCount = document.querySelectorAll(eventSelector).length;
                    const button = document.querySelector(buttonSelector);
                    const buttonVisible = !!button && !!(
                        button.offsetWidth ||
                        button.offsetHeight ||
                        button.getClientRects().length
                    );
                    return eventCount > previousCount || !buttonVisible;
                }""",
                arg=[EVENT_SELECTOR, LOAD_MORE_SELECTOR, previous_count],
                timeout=15_000,
            )
        except PlaywrightTimeoutError:
            current_count = page.locator(EVENT_SELECTOR).count()
            if current_count <= previous_count:
                return
    raise RuntimeError(f"Stopped after {max_clicks} load-more clicks")


def extract_events(page: Any) -> list[dict[str, str]]:
    raw_events: list[dict[str, str]] = page.eval_on_selector_all(
        EVENT_SELECTOR,
        """(articles) => articles.map((article) => {
            const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
            const text = (selector) => clean(article.querySelector(selector)?.textContent);
            let monthHeading = "";
            let sibling = article.previousElementSibling;
            while (sibling) {
                if (sibling.classList.contains("mec-month-divider")) {
                    monthHeading = clean(sibling.querySelector("h5")?.textContent);
                    break;
                }
                sibling = sibling.previousElementSibling;
            }
            const categories = Array.from(
                article.querySelectorAll(".mec-categories .mec-category a")
            ).map((node) => clean(node.textContent)).filter(Boolean);
            return {
                name: text(".mec-event-title"),
                date_label: text(".mec-start-date-label"),
                month_heading: monthHeading,
                start_time: text(".mec-start-time"),
                end_time: text(".mec-end-time"),
                event_type: categories.join("; "),
                description: text(".mec-event-description"),
                article_text: clean(article.textContent),
            };
        })""",
    )

    events = []
    seen: set[tuple[str, str, str]] = set()
    for raw_event in raw_events:
        name = clean_text(raw_event.get("name"))
        date = parse_event_date(
            clean_text(raw_event.get("date_label")),
            clean_text(raw_event.get("month_heading")),
        )
        time = build_time_range(
            clean_text(raw_event.get("start_time")),
            clean_text(raw_event.get("end_time")),
        )
        event_type = clean_text(raw_event.get("event_type")) or "Unknown"
        description = clean_text(raw_event.get("description"))
        article_text = clean_text(raw_event.get("article_text"))

        key = (name, date, time)
        if not name or key in seen:
            continue
        seen.add(key)
        events.append(
            {
                "event name": name,
                "date": date,
                "time": time,
                "event type": event_type,
                "has drink specials": event_has_drink_specials(
                    name, event_type, description, article_text
                ),
            }
        )
    return events


def scrape_events(
    url: str,
    max_clicks: int,
    timeout_ms: int,
    browser_executable: str | None,
) -> list[dict[str, str]]:
    with sync_playwright() as playwright:
        launch_options: dict[str, Any] = {
            "headless": True,
            "args": ["--no-sandbox"],
        }
        executable = browser_executable or detect_chrome()
        if executable:
            launch_options["executable_path"] = executable

        browser = playwright.chromium.launch(**launch_options)
        try:
            page = browser.new_page()
            page.set_default_timeout(timeout_ms)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_selector(EVENT_SELECTOR, timeout=timeout_ms)
            click_all_load_more(page, max_clicks=max_clicks)
            return extract_events(page)
        finally:
            browser.close()


def write_csv(events: list[dict[str, str]], output_path: Path) -> None:
    fieldnames = ["event name", "date", "time", "event type", "has drink specials"]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Slim's Dive Bar events and write them to CSV."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Events page URL to scrape")
    parser.add_argument(
        "--output",
        default="slims_events.csv",
        type=Path,
        help="CSV output path",
    )
    parser.add_argument(
        "--max-clicks",
        default=50,
        type=int,
        help="Maximum number of Load More clicks before stopping",
    )
    parser.add_argument(
        "--timeout-ms",
        default=30_000,
        type=int,
        help="Browser action timeout in milliseconds",
    )
    parser.add_argument(
        "--browser-executable",
        default=None,
        help="Optional Chrome/Chromium executable path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events = scrape_events(
        url=args.url,
        max_clicks=args.max_clicks,
        timeout_ms=args.timeout_ms,
        browser_executable=args.browser_executable,
    )
    write_csv(events, args.output)
    print(f"Wrote {len(events)} events to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
