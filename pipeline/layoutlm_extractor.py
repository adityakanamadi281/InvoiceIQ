from transformers import AutoProcessor, AutoModelForTokenClassification
import torch

processor = AutoProcessor.from_pretrained("microsoft/layoutlmv3-base")
model = AutoModelForTokenClassification.from_pretrained(
    "microsoft/layoutlmv3-base"
)

def extract_with_layoutlm(image):
    encoding = processor(image, return_tensors="pt")
    outputs = model(**encoding)

    logits = outputs.logits
    preds = torch.argmax(logits, dim=-1)

    return str(preds.tolist())  
