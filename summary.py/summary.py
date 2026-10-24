import csv
import json
import time
from collections import Counter
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
DELAY_SECONDS = 1

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}

# Configure retries for temporary request failures
session = requests.Session()
session.headers.update(HEADERS)

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    respect_retry_after_header=True
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


def scrape_books():
    books = []
    next_url = START_URL
    visited_urls = set()

    while next_url and next_url not in visited_urls:
        visited_urls.add(next_url)
        print("Scraping:", next_url)

        try:
            response = session.get(next_url, timeout=20)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"Request failed: {error}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        for item in soup.select("article.product_pod"):
            title_tag = item.select_one("h3 a")
            price_tag = item.select_one(".price_color")
            rating_tag = item.select_one(".star-rating")
            stock_tag = item.select_one(".availability")

            if not all([title_tag, price_tag, rating_tag, stock_tag]):
                continue

            rating_word = next(
                (
                    word for word in rating_tag.get("class", [])
                    if word in ["One", "Two", "Three", "Four", "Five"]
                ),
                ""
            )

            rating_map = {
                "One": 1,
                "Two": 2,
                "Three": 3,
                "Four": 4,
                "Five": 5
            }

            price_text = (
                price_tag.get_text(strip=True)
                .replace("Â£", "")
                .replace("£", "")
            )

            books.append({
                "title": title_tag.get("title", title_tag.get_text(strip=True)),
                "price": price_text,
                "rating": rating_map.get(rating_word, ""),
                "availability": " ".join(
                    stock_tag.get_text(" ", strip=True).split()
                )
            })

        next_tag = soup.select_one("li.next a")
        next_url = (
            urljoin(next_url, next_tag["href"])
            if next_tag and next_tag.get("href")
            else None
        )

        # Respect the website by waiting between page requests
        if next_url:
            time.sleep(DELAY_SECONDS)

    return books


def save_outputs(books):
    columns = ["title", "price", "rating", "availability"]

    # Save CSV output
    with open("books_data.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(books)

    # Save JSON output
    with open("books_data.json", "w", encoding="utf-8") as file:
        json.dump(books, file, indent=4, ensure_ascii=False)


def generate_report(books):
    prices = []

    for book in books:
        try:
            prices.append(float(book["price"]))
        except (ValueError, TypeError):
            continue

    ratings = Counter(
        str(book["rating"]) for book in books if book["rating"] != ""
    )

    if prices:
        average_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
    else:
        average_price = min_price = max_price = 0

    report = [
        "WEB SCRAPING SUMMARY REPORT",
        "=" * 30,
        f"Total books extracted: {len(books)}",
        f"Books with valid prices: {len(prices)}",
        f"Average price: £{average_price:.2f}",
        f"Minimum price: £{min_price:.2f}",
        f"Maximum price: £{max_price:.2f}",
        "",
        "Rating distribution:"
    ]

    for rating in sorted(ratings):
        report.append(f"{rating} star(s): {ratings[rating]} books")

    report.extend([
        "",
        "Output files:",
        "- books_data.csv",
        "- books_data.json",
        "- summary_report.txt"
    ])

    with open("summary_report.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(report) + "\n")

    print("\n".join(report))


def main():
    books = scrape_books()

    if not books:
        print("No books extracted. Check your internet connection and website.")
        return

    save_outputs(books)
    generate_report(books)

    print("\nScraping pipeline completed successfully!")


if __name__ == "__main__":
    main()