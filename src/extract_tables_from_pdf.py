import pdfplumber
import pandas as pd
import numpy as np
import re
import argparse
import json

def extract_tables_from_pdf(pdf_path, table_mapping):
    """
    Extract tables from specified pages of a PDF file using pdfplumber's line extraction.
    
    Args:
        pdf_path (str): Path to the PDF file
        pages (list): List of page numbers (1-based) containing tables
    
    Returns:
        list: List of pandas DataFrames containing species data
    """
    tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        current_data = []
        current_class = None
        
        for page_num, mapunit_ids in table_mapping.items():
            # pdfplumber uses 0-based indexing
            page = pdf.pages[page_num - 1]
            
            # Get all lines from the page
            lines = page.extract_text_lines()
            
            for line in lines:
                text = line['text'].strip()
                
                # Skip empty lines
                if not text:
                    continue
                    
                # Stop if we hit an appendix footer (e.g., "A - 6")
                if re.match(r'^[A-Z] - \d+$', text):
                    break

                # Skip the "Stand Table" header and other non-data lines
                if text in ['Stand Table', 'Lifeform Species Name Con Avg Min Max D Ch Ab Oft', 'January 2012'] or 'January' in text:
                    continue

                # Check if this is a classification line
                if text in ['Tree', 'Shrub', 'Herb', 'Nonvascular']:
                    current_class = text
                    continue

                # Try to parse the data line
                parts = text.split()
                if len(parts) >= 5:  # Need at least species name and 4 numbers
                    try:
                        # Find where the numbers start
                        for i, part in enumerate(parts):
                            if re.match(r'^\d+(?:\.\d+)?$', part):
                                numeric_start = i
                                break
                        else:
                            continue
                        
                        species_name = ' '.join(parts[:numeric_start])
                        numbers = parts[numeric_start:numeric_start+4]
                        
                        # Convert numbers to float
                        con, avg, min_val, max_val = map(float, numbers)
                        
                        for mapunit_id in mapunit_ids:
                            current_data.append({
                                'MapUnitId': mapunit_id,
                                'Species': species_name,
                                'Class': current_class,
                                'Con': con,
                                'Avg': avg,
                                'Min': min_val,
                                'Max': max_val
                            })
                    except (ValueError, IndexError):
                        print(f"Failed to parse line in mapunit {mapunit_id}: {text}")
                        continue
            
            # Create DataFrame for this page if we have data
            if current_data:
                df = pd.DataFrame(current_data)
                tables.append(df)
                current_data = []  # Reset for next page
            print(f"Finished mapUnitId: {mapunit_id}")

    return tables

def clean_table(df):
    """
    Clean the extracted table by fixing data types and handling missing values.
    """
    # Convert numeric columns to float
    numeric_cols = ['Con', 'Avg', 'Min', 'Max']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort by Class and Species
    df = df.sort_values(['Class', 'Species'])
    
    return df

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--pdf", help="Path to the PDF file", required=True)
    argparser.add_argument("--table_mapping_json", help="Mapping of MapUnitId to the page containing the stand table", required=True)
    args = argparser.parse_args()

    # pages_with_tables = json.loads(args.table_mapping_json)

    pages_with_tables = {
        12: ["10161"],
        16: ["15030"],
        19: ["15110"],
        24: ["21234"],
        26: ["21210"],
        33: ["22030"],
        38: ["28020", "28023"],
        40: ["24010"],
        44: ["28130", "28060"],
        47: ["28134"],
        50: ["28133"],
        54: ["10020", "10025"],
        57: ["10032"],
        60: ["10031"],
        63: ["28190", "28192"],
        67: ["59010", "59011"],
        69: ["59012"]
    }


    tables = extract_tables_from_pdf(args.pdf, pages_with_tables)

    for i, table in enumerate(tables):
        table = clean_table(table)
        print(f"\nTable {i+1}:")
        print(table)
        
        # Optionally save to CSV
        table.to_csv(f'table_{i+1}.csv', index=False)