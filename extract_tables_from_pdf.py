import pdfplumber
import pandas as pd
import numpy as np
import re
import argparse

def extract_tables_from_pdf(pdf_path, pages):
    """
    Extract tables from specified pages of a PDF file using pdfplumber.
    
    Args:
        pdf_path (str): Path to the PDF file
        pages (list): List of page numbers (1-based) containing tables
    
    Returns:
        list: List of pandas DataFrames, one for each extracted table
    """
    tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in pages:
            # pdfplumber uses 0-based indexing
            page = pdf.pages[page_num - 1]
            
            # Extract tables from the page
            page_tables = page.extract_tables()
            
            for table in page_tables:
                # Skip empty tables
                if not table:
                    continue
                
                # Initialize lists to store data
                data = []
                current_lifeform = None
                headers = ['Lifeform', 'Species Name', 'Con', 'Avg', 'Min', 'Max', 'D', 'Ch', 'Ab', 'Oft']
                
                # Process each row in the table
                for row in table:
                    # Clean row data (remove None and empty strings)
                    row = [str(cell).strip() if cell is not None else '' for cell in row]
                    row = [cell for cell in row if cell]
                    
                    if not row:
                        continue
                    
                    # Check if this is a lifeform row
                    if any(form in row[0] for form in ['Tree', 'Shrub', 'Herb', 'Nonvascular']):
                        current_lifeform = row[0]
                        continue
                    
                    # Skip header rows
                    if 'Species Name' in ' '.join(row):
                        continue
                    
                    # Process data row
                    species_name = []
                    numbers = []
                    indicators = []
                    numeric_found = False
                    
                    for cell in row:
                        if not numeric_found and not re.match(r'^[\d.]+$', cell):
                            species_name.append(cell)
                        else:
                            numeric_found = True
                            if re.match(r'^[\d.]+$', cell):
                                numbers.append(float(cell))
                            elif cell.upper() in ['X', 'x']:
                                indicators.append('X')
                            else:
                                indicators.append('')
                    
                    if species_name:
                        # Combine species name parts
                        species_name = ' '.join(species_name)
                        
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