
import csv
import requests
from bs4 import BeautifulSoup

url = "https://books.toscrape.com/catalogue/page-1.html"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

books = []

for item in soup.select("article.product_pod"):
    title_tag = item.select_one("h3 a")
    price_tag = item.select_one(".price_color")
    rating_tag = item.select_one(".star-rating")
    stock_tag = item.select_one(".availability")

    if not all([title_tag, price_tag, rating_tag, stock_tag]):
        continue

    rating_classes = rating_tag.get("class", [])
    rating_word = next(
        (word for word in rating_classes
         if word in ["One", "Two", "Three", "Four", "Five"]),
        ""
    )

    rating_map = {
        "One": 1, "Two": 2, "Three": 3,
        "Four": 4, "Five": 5
    }

    books.append({
        "title": title_tag.get("title", title_tag.get_text(strip=True)),
        "price": price_tag.get_text(strip=True).replace("£", ""),
        "rating": rating_map.get(rating_word, ""),
        "availability": " ".join(
            stock_tag.get_text(" ", strip=True).split()
        )
    })

with open("books_data.csv", "w", newline="", encoding="utf-8-sig") as file:
    columns = ["title", "price", "rating", "availability"]
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(books)

print("Scraping completed successfully!")
print("Total books extracted:", len(books))
print("Data saved to books_data.csv")

