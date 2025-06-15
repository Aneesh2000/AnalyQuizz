import PyPDF2
import pdfplumber
import os

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF using both PyPDF2 and pdfplumber as fallback.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
        
    Raises:
        Exception: If text extraction fails
    """
    if not os.path.exists(file_path):
        raise Exception("PDF file not found")
    
    extracted_text = ""
    
    # First try with PyPDF2
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        
        # If we got substantial text, return it
        if len(extracted_text.strip()) > 50:
            return extracted_text.strip()
    
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
    
    # Fallback to pdfplumber if PyPDF2 didn't work well
    try:
        with pdfplumber.open(file_path) as pdf:
            extracted_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        
        if extracted_text.strip():
            return extracted_text.strip()
        else:
            raise Exception("No text could be extracted from the PDF")
    
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def validate_pdf_content(extracted_text: str) -> bool:
    """
    Validate if the extracted text is suitable for quiz generation.
    
    Args:
        extracted_text (str): The extracted text from PDF
        
    Returns:
        bool: True if content is valid for quiz generation
    """
    if not extracted_text or len(extracted_text.strip()) < 100:
        return False
    
    # Check if it's mostly gibberish or encoded content
    printable_chars = sum(1 for c in extracted_text if c.isprintable() or c.isspace())
    if printable_chars / len(extracted_text) < 0.8:
        return False
    
    # Check if it has reasonable word structure
    words = extracted_text.split()
    if len(words) < 50:
        return False
    
    return True

def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text for better processing.
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    # Remove excessive whitespace
    import re
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]{}\'\"\/]', '', text)
    
    return text.strip() 