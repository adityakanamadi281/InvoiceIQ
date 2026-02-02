from dateutil import parser
import re

def clean_date(d):
    try:
        return parser.parse(d).strftime("%Y-%m-%d")
    except:
        return None

def clean_money(x):
    if x is None:
        return 0
    x = re.sub(r"[^\d.]", "", str(x))
    return float(x) if x else 0

def normalize(data):
    data["date"] = clean_date(data.get("date"))
    data["total_amount"] = clean_money(data.get("total_amount"))

    for item in data.get("line_items", []):
        item["quantity"] = float(item.get("quantity", 0))
        item["unit_price"] = clean_money(item.get("unit_price"))
        item["line_total"] = clean_money(item.get("line_total"))

    return data
