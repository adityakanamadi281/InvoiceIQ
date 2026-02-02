import easyocr
from PIL import Image
import os

try:
    from pdf2image import convert_from_path
    POPPLER_AVAILABLE = True
except:
    POPPLER_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except:
    PYPDF_AVAILABLE = False

# Initialize EasyOCR reader (will download model on first use)
reader = easyocr.Reader(['en'])

def extract_text_from_pdf_pypdf(pdf_path):
    """Try to extract text directly from PDF using pypdf."""
    if not PYPDF_AVAILABLE:
        return None
    try:
        text_content = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
        full_text = "\n".join(text_content)
        if full_text.strip():  # Only return if we got actual text
            return full_text
    except:
        pass
    return None

def pdf_to_images(pdf_path):
    """Convert PDF to images. Requires poppler to be installed."""
    if not POPPLER_AVAILABLE:
        raise Exception("pdf2image not available - Poppler may not be installed")
    return convert_from_path(pdf_path, dpi=300)

def ocr_image(image: Image.Image):
    """Extract text from image using EasyOCR."""
    # Ensure image is in RGB mode
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    results = reader.readtext(image)
    
    # Extract text from results
    text = "\n".join([result[1] for result in results])
    return text

def extract_text(file_path):
    """Extract text from PDF or image file."""
    texts = []

    if file_path.lower().endswith(".pdf"):
        # First, try to extract text directly from PDF
        pdf_text = extract_text_from_pdf_pypdf(file_path)
        if pdf_text:
            return pdf_text
        
        # If direct extraction failed, try image-based OCR
        try:
            pages = pdf_to_images(file_path)
            for page in pages:
                texts.append(ocr_image(page))
        except Exception as e:
            raise Exception(f"Failed to process PDF: {e}")
    else:
        try:
            img = Image.open(file_path)
            texts.append(ocr_image(img))
        except Exception as e:
            raise Exception(f"Failed to process image: {e}")

    return "\n".join(texts)
