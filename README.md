Invoice Extraction with OCR + Gemma LLM (Hugging Face)
This project extracts structured data from multilingual invoice files using OCR and Google's Gemma LLM via Hugging Face Transformers. It supports .zip uploads containing .pdf, .jpg, .png, .gif invoice files — and intelligently extracts fields like Vendor, Date, and Total.

 Features
 Input: .zip file containing multiple invoice formats (.pdf, .jpg, .png, .gif)

 LLM-powered extraction using gemma-1.1-2b-it (supports French + English)

 Extracts fields:

Vendor name

Invoice number

Date

Product and Quantity

Subtotal, Taxes, Total

Payment method

 OCR support for both images and PDFs using EasyOCR and pdf2image

 Disk offloading to run on low-RAM CPUs (no GPU needed)

 Fully local — no internet required after first download
 
 Prerequisites
To run this project, make sure you have the following tools installed:
1. Anaconda / Miniconda
2. Tesseract OCR (Optional)
3. Poppler for Windows - Set your path in script (POPPLER_PATH = r"C:\\path\\to\\poppler\\bin")
4. Python Packages (pip install easyocr pdf2image Pillow opencv-python transformers accelerate torch)
5. Ollama and  gemma-1.1-2b-it
   
