
import csv
from pathlib import Path
from statistics import mean

csv_file = Path("books_data.csv")

if not csv_file.exists():
    print("Error: books_data.csv file not found!")
else:
    with csv_file.open("r", encoding="utf-8-sig", newline="") as file:
        books = list(csv.DictReader(file))

    if not books:
        print("No book data found in CSV!")
    else:
        prices = [
           float(
    book["price"]
    .replace("£", "")
    .replace("Â", "")
    .strip()
)
            for book in books
        ]

        report = [
            "AUTOMATED WEB SCRAPING REPORT",
            "=" * 35,
            f"Total books extracted: {len(books)}",
            f"Average price: £{mean(prices):.2f}",
            f"Minimum price: £{min(prices):.2f}",
            f"Maximum price: £{max(prices):.2f}",
        ]

        report_file = Path("summary_report.txt")
        report_file.write_text("\n".join(report), encoding="utf-8")

        print("\n".join(report))
        print("\nReport saved to summary_report.txt")
