import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import numpy as np
import re
import argparse

def extract_tables_from_pdf(pdf_path, pages):
    """
    Extract tables from specified pages of a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        pages (list): List of page numbers (1-based) containing tables
    
    Returns:
        list: List of pandas DataFrames, one for each extracted table
    """
    # Convert PDF pages to images
    images = convert_from_path(pdf_path, first_page=min(pages), last_page=max(pages))
    
    # Initialize list to store DataFrames
    tables = []
    
    for img in images:
        # Extract text from image using pytesseract
        text = pytesseract.image_to_string(img)
        
        # Split text into lines
        lines = text.split('\n')
        
        # Remove empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        # Find the header line to determine columns
        header_idx = -1
        for i, line in enumerate(lines):
            if 'Species Name' in line:
                header_idx = i
                break
        
        if header_idx == -1:
            continue
            
        # Extract column headers
        headers = ['Lifeform', 'Species Name', 'Con', 'Avg', 'Min', 'Max', 'D', 'Ch', 'Ab', 'Oft']
        
        # Initialize lists to store data
        data = []
        current_lifeform = None
        
        # Process each line after the header
        for line in lines[header_idx + 1:]:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if this is a lifeform line
            if any(form in line for form in ['Tree', 'Shrub', 'Herb', 'Nonvascular']):
                current_lifeform = line.strip()
                continue
            
            # Split the line into components
            parts = line.split()
            
            if len(parts) < 4:  # Skip lines that don't have enough data
                continue
                
            # Extract species name (may contain multiple words)
            species_name = []
            numeric_found = False
            for part in parts:
                if re.match(r'^[\d.]+$', part):
                    numeric_found = True
                    break
                species_name.append(part)
            species_name = ' '.join(species_name)
            
            # Extract numeric values and indicators
            numbers = []
            indicators = []
            for part in parts[len(species_name.split()):]:
                if re.match(r'^[\d.]+$', part):
                    numbers.append(float(part))
                elif part in ['X', 'x']:
                    indicators.append('X')
                else:
                    indicators.append('')
            
            # Pad numbers and indicators to match expected length
            numbers.extend([np.nan] * (4 - len(numbers)))  # Con, Avg, Min, Max
            indicators.extend([''] * (4 - len(indicators)))  # D, Ch, Ab, Oft
            
            # Combine all data
            row_data = [current_lifeform, species_name] + numbers + indicators
            data.append(row_data)
        
        if data:
            # Create DataFrame
            df = pd.DataFrame(data, columns=headers)
            tables.append(df)
    
    return tables

def clean_table(df):
    """
    Clean the extracted table by fixing data types and handling missing values.
    """
    # Convert numeric columns to float
    numeric_cols = ['Con', 'Avg', 'Min', 'Max']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert indicator columns to categorical
    indicator_cols = ['D', 'Ch', 'Ab', 'Oft']
    for col in indicator_cols:
        df[col] = df[col].replace('', np.nan)
    
    return df

# Example usage
if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--pdf", help="Path to the PDF file", required=True)
    argparser.add_argument("--pages", help="Comma-separated list of page numbers containing tables", required=True)
    args = argparser.parse_args()

    pages_with_tables = [int(page) for page in args.pages.split(',')]

    tables = extract_tables_from_pdf(args.pdf, pages_with_tables)

    for i, table in enumerate(tables):
        table = clean_table(table)
        print(f"\nTable {i+1}:")
        print(table)