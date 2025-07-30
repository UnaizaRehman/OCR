import os
import fitz  # PyMuPDF
import tempfile
import zipfile
import rarfile
import shutil
import easyocr
import json
import pandas as pd
import subprocess
from PIL import Image
from datetime import datetime

# Hardcoded archive paths
ZIP_PATH = r"C:\Users\hp\OneDrive\Desktop\Uni Docs\Projects\OCR\factures 3.zip"
RAR_PATH = r"C:\Users\hp\OneDrive\Desktop\Uni Docs\Projects\OCR\invoices3.rar"

# Fields to extract
REQUIRED_FIELDS = [
    "Vendor Name", "Invoice Number", "Date",
    "Product & Quantity", "Subtotal", "Taxes",
    "Total", "Payment Method"
]

# Setup
rarfile.UNRAR_TOOL = r"C:\Users\hp\OneDrive\Desktop\UnRAR.exe"
reader = easyocr.Reader(['en', 'fr'], gpu=False)

def extract_zip(zip_path):
    temp_dir = tempfile.mkdtemp()
    print(f"[📦] Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def extract_rar(rar_path):
    temp_dir = tempfile.mkdtemp()
    print(f"[📦] Extracting RAR file...")
    with rarfile.RarFile(rar_path) as rf:
        rf.extractall(temp_dir)
    return temp_dir

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        if not text.strip():
            images = []
            for page in fitz.open(pdf_path):
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            for img in images:
                ocr_result = reader.readtext(np.array(img), detail=0, paragraph=True)
                text += "\n".join(ocr_result)
    except Exception as e:
        print(f"[⚠️] Failed OCR for {pdf_path}: {e}")
    return text

def query_gemma_2b(invoice_text):
    prompt = (
        "Extract the following fields from the invoice text below:\n"
        "Vendor Name, Invoice Number, Date, Product & Quantity, Subtotal, Taxes, Total, Payment Method.\n\n"
        "Output strictly in JSON format with these fields only.\n\n"
        f"Invoice Text:\n{invoice_text}"
    )

    try:
        result = subprocess.run(
            ["ollama", "run", "gemma:2b", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",  
            timeout=180  # Increase timeout for longer prompts
        )
        if result.returncode != 0:
            print("[❌] Gemma failed:", result.stderr)
            return {}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("[⏰] Gemma timed out after 180 seconds")
        return {}
    except json.JSONDecodeError:
        print("[❌] Failed to decode JSON from Gemma output")
        print("[🪵] Raw Output:\n", result.stdout[:1000])  # Debug output
        return {}


def process_all_invoices_from_folder(folder):
    all_results = []
    for root, _, files in os.walk(folder):
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext not in ['pdf', 'png', 'jpg', 'jpeg']:
                continue

            filepath = os.path.join(root, f)
            print(f"\n[📄] PROCESSING: {filepath}")
            raw_text = extract_text_from_pdf(filepath)
            print(f"[🔍] OCR TEXT (first 500 chars):\n{raw_text[:500]}")

            if not raw_text.strip():
                print("[⚠️] OCR returned NO TEXT. Skipping.")
                continue

            result = query_gemma_2b(raw_text)
            print(f"[🤖] Gemma OUTPUT: {result}")

            if result and any(result.get(field) for field in REQUIRED_FIELDS):
                row = {key: result.get(key, "") for key in REQUIRED_FIELDS}
                all_results.append(row)
            else:
                print("[⚠️] Gemma returned empty or incomplete fields. Skipping.")

    return all_results


def save_outputs(results):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(os.getcwd(), "output_" + timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # Save Excel
    df = pd.DataFrame(results)
    df.to_excel(os.path.join(output_dir, "invoices.xlsx"), index=False)

    # Save JSON
    with open(os.path.join(output_dir, "invoices.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {output_dir}")

def main():
    all_results = []
    for archive_path in [ZIP_PATH, RAR_PATH]:
        if archive_path.endswith(".zip"):
            folder = extract_zip(archive_path)
        elif archive_path.endswith(".rar"):
            folder = extract_rar(archive_path)
        else:
            continue
        results = process_all_invoices_from_folder(folder)
        all_results.extend(results)
        shutil.rmtree(folder, ignore_errors=True)
    if all_results:
        save_outputs(all_results)
    else:
        print("[❌] No results extracted.")

if __name__ == "__main__":
    print("Using CPU. Note: This module is much faster with a GPU.")
    main()
