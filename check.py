import pdfplumber

with pdfplumber.open("data/raw/NCO_2015_Vol_II_Part1.pdf") as pdf:
    # Show first 3 pages
    for i in range(min(3, len(pdf.pages))):
        print(f"\n{'='*60}")
        print(f"PAGE {i+1}")
        print('='*60)
        
        page = pdf.pages[i]
        
        # Show raw text
        print("\n--- RAW TEXT ---")
        print(page.extract_text()[:2000])  # First 2000 chars
        
        # Show word positions
        print("\n--- WORD POSITIONS (first 20 words) ---")
        words = page.extract_words()[:20]
        for w in words:
            print(f"x={w['x0']:6.1f} y={w['top']:6.1f} text='{w['text']}'")