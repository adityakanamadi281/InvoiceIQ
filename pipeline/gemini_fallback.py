import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")

PROMPT = """Extract invoice information and return ONLY valid JSON (no markdown, no explanations, start with {{ and end with }}):

{{
  "invoice_number": "extracted number or empty string",
  "date": "extracted date or empty string",
  "vendor": "extracted vendor/supplier name or empty string",
  "total_amount": "total amount or empty string",
  "line_items": [
    {{
      "description": "item description or empty string",
      "quantity": "qty or empty string",
      "unit_price": "price or empty string",
      "line_total": "total or empty string"
    }}
  ]
}}

Extract from this text:
{}"""

def extract_json_from_text(text):
    """Extract JSON from text that might be wrapped in markdown code blocks."""
    # Try to find JSON in markdown code blocks first
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find plain JSON object
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    return text

def extract_invoice_number(text):
    """Extract invoice number using regex patterns."""
    # Look for common invoice number patterns
    patterns = [
        r'INVOICE\s*(?:NO|NUMBER|#)?\s*[:=\s]+(\d+)',
        r'INV\s*[:=\s]+(\d+)',
        r'INVOICE\s*(\d+)',
        r'(?:Invoice|INVOICE).*?(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Return first large number that looks like an invoice
    numbers = re.findall(r'\b\d{5,}\b', text)
    if numbers:
        return numbers[0]
    
    return ""

def extract_date(text):
    """Extract date using regex patterns."""
    # Look for common date patterns
    patterns = [
        r'(?:INVOICE\s+)?DATE[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""

def extract_vendor(text):
    """Extract vendor/supplier name from text."""
    # Look for "Sold To:" or "From:" patterns
    patterns = [
        r'(?:SOLD\s+TO|FROM|VENDOR)[:\s]+([^\n]+)',
        r'^([A-Z][^\n]{10,40})\s*(?:LLC|INC|CO|CORP)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    
    return ""

def extract_total(text):
    """Extract total amount from text."""
    # Look for total patterns
    patterns = [
        r'TOTAL[:\s]+\$?\s*([\d,]+\.?\d*)',
        r'(?:TOTAL|AMOUNT\s+DUE)[:\s=]+\$?\s*([\d,]+\.?\d*)',
        r'TOTAL\s*(?:DUE)?\s*[=:]\s*\$?\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""

def extract_with_fallback_parsing(text):
    """Extract invoice data using pattern matching when API fails."""
    data = {
        "invoice_number": extract_invoice_number(text),
        "date": extract_date(text),
        "vendor": extract_vendor(text),
        "total_amount": extract_total(text),
        "line_items": []
    }
    
    # Try to extract line items
    line_patterns = r'(\d+)\s+(.{10,50}?)\s+([\d.]+)\s+\$?\s*([\d,.]+)'
    matches = re.findall(line_patterns, text)
    
    for match in matches[:10]:  # Limit to first 10 items
        item = {
            "description": match[1].strip(),
            "quantity": match[0].strip(),
            "unit_price": match[3].strip(),
            "line_total": match[3].strip()
        }
        data["line_items"].append(item)
    
    return data

def extract_with_gemini(text):
    try:
        # Limit text to first 3000 chars to avoid token limits
        truncated_text = text[:3000] if text else ""
        
        resp = model.generate_content(PROMPT.format(truncated_text), timeout=10)
        
        if not resp.text:
            return extract_with_fallback_parsing(text)
        
        # Extract JSON from response (handles markdown code blocks)
        json_text = extract_json_from_text(resp.text)
        
        # Parse JSON
        data = json.loads(json_text)
        
        # Ensure required structure exists
        if "line_items" not in data:
            data["line_items"] = []
        
        return data
    except json.JSONDecodeError:
        # If JSON parsing fails, use fallback pattern matching
        return extract_with_fallback_parsing(text)
    except Exception as e:
        # If API fails (quota, auth, etc.), use fallback pattern matching
        return extract_with_fallback_parsing(text)
