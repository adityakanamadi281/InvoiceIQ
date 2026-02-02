from pipeline.processor import process_folder
from pipeline.schema import save_to_csv
import pandas as pd

folder = r"C:\Users\adity\InvoiceIQ\data\Invoices - Take Home Assignment"

print(f"Processing invoices from: {folder}")
invoices = process_folder(folder)

print(f"Total invoices processed: {len(invoices)}")

if invoices:
    save_to_csv(invoices)
    print("CSV files saved successfully!")
    
    df = pd.DataFrame(invoices)
    print(df.head())
else:
    print("No invoices were processed.")
