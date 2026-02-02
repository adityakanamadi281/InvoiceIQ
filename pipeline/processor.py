import os
from .ocr import extract_text
from .gemini_fallback import extract_with_gemini
from .validator import normalize

def process_folder(folder):

    results = []
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png'))]
    print(f"Found {len(files)} invoice files")

    for f in files:
        path = os.path.join(folder, f)

        try:
            print(f"Processing: {f}")
            text = extract_text(path)
            
            if not text or not text.strip():
                print(f"  FAILED: No text extracted from file")
                continue

            data = extract_with_gemini(text)

            if not data:
                print(f"  FAILED: Could not parse invoice data")
                continue

            data = normalize(data)
            results.append(data)
            print(f"  SUCCESS - Invoice #: {data.get('invoice_number', 'N/A')}")

        except Exception as e:
            print(f"  FAILED: {str(e)}")

    return results
