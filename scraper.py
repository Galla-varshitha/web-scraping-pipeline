
import csv
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import Counter
from statistics import mean

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; BookScraper/1.0)"
}

# Retry failed requests
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

session = requests.Session()
session.headers.update(headers)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

books = []

rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

# Scrape the first 3 pages
for page in range(1, 4):
    if page > 1:
        time.sleep(1)  # Rate limiting

    url = BASE_URL.format(page)
    response = session.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for item in soup.select("article.product_pod"):
        title_tag = item.select_one("h3 a")
        price_tag = item.select_one(".price_color")
        rating_tag = item.select_one(".star-rating")
        stock_tag = item.select_one(".availability")

        if not all([title_tag, price_tag, rating_tag, stock_tag]):
            continue

        rating_word = next(
            (word for word in rating_tag.get("class", [])
             if word in rating_map),
            ""
        )

        price_text = (
            price_tag.get_text(strip=True)
            .replace("£", "")
            .replace("Â", "")
        )

        books.append({
            "title": title_tag.get("title", title_tag.get_text(strip=True)),
            "price": price_text,
            "rating": rating_map.get(rating_word, ""),
            "availability": " ".join(
                stock_tag.get_text(" ", strip=True).split()
            )
        })

# Save structured CSV
columns = ["title", "price", "rating", "availability"]

with open("books_data.csv", "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(books)

# Generate summary statistics
prices = [float(book["price"]) for book in books if book["price"]]
ratings = [int(book["rating"]) for book in books if book["rating"]]
availability_counts = Counter(book["availability"] for book in books)

with open("summary_report.txt", "w", encoding="utf-8") as file:
    file.write("BOOK SCRAPING SUMMARY REPORT\n")
    file.write("============================\n")
    file.write(f"Total books extracted: {len(books)}\n")

    if prices:
        file.write(f"Average price: GBP {mean(prices):.2f}\n")
file.write(f"Minimum price: GBP {min(prices):.2f}\n")
file.write(f"Maximum price: GBP {max(prices):.2f}\n")
        file.write(f"Minimum price: £{min(prices):.2f}\n")
        file.write(f"Maximum price: £{max(prices):.2f}\n")

    if ratings:
        file.write(f"Average rating: {mean(ratings):.2f}/5\n")

    file.write("\nAvailability counts:\n")
    for status, count in availability_counts.items():
        file.write(f"{status}: {count}\n")

session.close()

print("Scraping completed successfully!")
print("Total books extracted:", len(books))
print("Data saved to books_data.csv")
print("Report saved to summary_report.txt")
