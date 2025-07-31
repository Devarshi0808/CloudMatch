import pandas as pd
import numpy as np

def analyze_excel_file():
    """Analyze the structure and content of the Vendors_and_Products.xlsx file"""
    
    try:
        # Read the Excel file
        print("Reading Excel file: Vendors_and_Products.xlsx")
        df = pd.read_excel('Vendors_and_Products.xlsx')
        
        print("\n" + "="*50)
        print("EXCEL FILE ANALYSIS")
        print("="*50)
        
        # Basic information
        print(f"\n1. BASIC INFORMATION:")
        print(f"   - Number of rows: {len(df)}")
        print(f"   - Number of columns: {len(df.columns)}")
        print(f"   - Column names: {list(df.columns)}")
        
        # Data types
        print(f"\n2. DATA TYPES:")
        for col in df.columns:
            print(f"   - {col}: {df[col].dtype}")
        
        # Sample data
        print(f"\n3. FIRST 10 ROWS:")
        print(df.head(10).to_string(index=False))
        
        # Check for missing values
        print(f"\n4. MISSING VALUES:")
        missing_data = df.isnull().sum()
        for col, missing_count in missing_data.items():
            if missing_count > 0:
                print(f"   - {col}: {missing_count} missing values")
            else:
                print(f"   - {col}: No missing values")
        
        # Unique values in key columns
        print(f"\n5. UNIQUE VALUES ANALYSIS:")
        for col in df.columns:
            unique_count = df[col].nunique()
            print(f"   - {col}: {unique_count} unique values")
            if unique_count <= 10:  # Show unique values if not too many
                print(f"     Values: {list(df[col].unique())}")
        
        # Check if there are multiple sheets
        print(f"\n6. EXCEL SHEETS:")
        xl_file = pd.ExcelFile('Vendors_and_Products.xlsx')
        print(f"   - Sheet names: {xl_file.sheet_names}")
        
        # If multiple sheets, analyze each
        if len(xl_file.sheet_names) > 1:
            print(f"\n7. MULTIPLE SHEETS ANALYSIS:")
            for sheet_name in xl_file.sheet_names:
                print(f"\n   Sheet: {sheet_name}")
                sheet_df = pd.read_excel('Vendors_and_Products.xlsx', sheet_name=sheet_name)
                print(f"   - Rows: {len(sheet_df)}, Columns: {len(sheet_df.columns)}")
                print(f"   - Columns: {list(sheet_df.columns)}")
                print(f"   - Sample data:")
                print(sheet_df.head(3).to_string())
        
        return df
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def show_detailed_sample():
    """Show a more detailed sample of the data"""
    try:
        df = pd.read_excel('Vendors_and_Products.xlsx')
        
        print("\n" + "="*60)
        print("DETAILED SAMPLE DATA")
        print("="*60)
        
        # Show first 20 rows
        print(f"\nFirst 20 entries:")
        print(df.head(20).to_string(index=False))
        
        # Show some random samples
        print(f"\nRandom 15 samples:")
        print(df.sample(n=15, random_state=42).to_string(index=False))
        
        # Show vendors with multiple products
        vendor_counts = df['vendor'].value_counts()
        print(f"\nVendors with multiple products:")
        multi_product_vendors = vendor_counts[vendor_counts > 1]
        print(multi_product_vendors.head(10))
        
        # Show some examples of vendors with multiple products
        print(f"\nExamples of vendors with multiple products:")
        for vendor in multi_product_vendors.head(5).index:
            products = df[df['vendor'] == vendor]['solution_name'].tolist()
            print(f"  {vendor}: {products}")
        
        return df
        
    except Exception as e:
        print(f"Error in detailed analysis: {e}")
        return None

if __name__ == "__main__":
    df = analyze_excel_file()
    print("\n" + "="*80)
    df_detailed = show_detailed_sample() 