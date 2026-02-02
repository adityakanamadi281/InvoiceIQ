import pandas as pd

def save_to_csv(invoices):
    invoice_rows = []
    item_rows = []

    for inv in invoices:
        invoice_rows.append([
            inv["invoice_number"],
            inv["vendor"],
            inv["date"],
            inv["total_amount"]
        ])

        for it in inv["line_items"]:
            item_rows.append([
                inv["invoice_number"],
                it["description"],
                it["quantity"],
                it["unit_price"],
                it["line_total"]
            ])

    pd.DataFrame(invoice_rows,
        columns=["invoice_number","vendor","date","total"]
    ).to_csv("invoices.csv", index=False)

    pd.DataFrame(item_rows,
        columns=["invoice_number","description","quantity","unit_price","total"]
    ).to_csv("line_items.csv", index=False)
