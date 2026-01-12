#!/usr/bin/env python3
"""
NCO-2015 Occupation Data Extractor - Two-Column PDF Layout
Extracts clean occupation records from Indian Government NCO-2015 PDFs.

Author: Senior Data Engineering Team
Purpose: Government AI system for occupation mapping
Version: 2.0 (Production - Two-Column Layout)
"""

import pdfplumber
import re
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Occupation:
    """Represents a single NCO occupation record."""
    nco_code: str
    title: str
    description: str
    
    def is_valid(self) -> bool:
        """Validates that all fields are properly populated."""
        return (
            bool(self.nco_code and self.nco_code.strip()) and
            bool(self.title and self.title.strip()) and
            bool(self.description and self.description.strip()) and
            len(self.nco_code) == 4 and
            self.nco_code.isdigit() and
            int(self.nco_code[0]) >= 1 and  # First digit 1-9
            len(self.title) > 3 and
            len(self.description) > 20  # Minimum meaningful description
        )


class NCOExtractor:
    """
    Extracts occupation data from NCO-2015 PDF files with two-column layout.
    
    Key insight: PDFs have two narrow columns that must be processed separately.
    """
    
    # Keywords that indicate structural headers (NOT occupations)
    HEADER_KEYWORDS = {
        'division', 'sub-division', 'subdivision', 'family', 'sub-family',
        'volume', 'part', 'section', 'chapter', 'index', 'contents',
        'classification', 'national', 'occupations', 'annexure', 'group',
        'preface', 'foreword', 'introduction'
    }
    
    # Keywords that indicate metadata sections to skip
    METADATA_KEYWORDS = {
        'qualification pack', 'qp-nos', 'qp nos', 'nsqf', 'nos code',
        'performance criteria', 'knowledge and understanding', 
        'sector', 'occupation map', 'nveqf', 'also known as'
    }
    
    # Patterns that indicate ISCO references (end of description)
    ISCO_PATTERNS = [
        r'isco[-\s]*08',
        r'unit group:?\s*\d{4}',
        r'sub-group:?\s*\d{3}',
    ]
    
    def __init__(self, pdf_paths: List[str]):
        """
        Initialize extractor with PDF file paths.
        
        Args:
            pdf_paths: List of paths to NCO-2015 PDF files
        """
        self.pdf_paths = [Path(p) for p in pdf_paths]
        self.occupations: List[Occupation] = []
        
    def is_valid_nco_code(self, text: str) -> bool:
        """
        Validates if text is a genuine 4-digit NCO occupation code.
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid NCO code
        """
        if not text or not text.isdigit():
            return False
            
        if len(text) != 4:
            return False
            
        # First digit must be 1-9
        if text[0] == '0':
            return False
            
        # Reject known false positives
        if text in {'2015', '2016', '2017', '2018', '2019', '2020', '2021'}:
            return False
            
        return True
    
    def is_header_line(self, line: str) -> bool:
        """Detects if line is a structural header."""
        line_lower = line.lower().strip()
        
        # Very short lines are likely headers
        if len(line_lower) < 5:
            return False
            
        # Check for header keywords
        for keyword in self.HEADER_KEYWORDS:
            if keyword in line_lower:
                return True
        
        # All caps with few words (but not occupation codes)
        words = line.split()
        if len(words) <= 6 and line.isupper():
            # But not if it starts with a valid code
            if words and not self.is_valid_nco_code(words[0]):
                return True
            
        return False
    
    def is_metadata_section(self, line: str) -> bool:
        """Detects if line is QP/NSQF metadata."""
        line_lower = line.lower().strip()
        
        for keyword in self.METADATA_KEYWORDS:
            if keyword in line_lower:
                return True
        
        # Detect sub-codes like 6111.0101
        if re.search(r'\d{4}\.\d{4}', line):
            return True
            
        # Detect QP code patterns
        if re.search(r'(agr|con|ite|css|ssc|ffs)/q\d+', line_lower):
            return True
            
        return False
    
    def should_stop_description(self, line: str) -> bool:
        """Determines if we've reached the end of occupation description."""
        line_lower = line.lower().strip()
        
        # Check for ISCO references
        for pattern in self.ISCO_PATTERNS:
            if re.search(pattern, line_lower):
                return True
        
        # Check for QP section start
        if 'qualification pack' in line_lower or 'qp-nos' in line_lower:
            return True
            
        return False
    
    def split_into_columns(self, page) -> Tuple[List[str], List[str]]:
        """
        Splits a two-column page into left and right columns.
        
        Args:
            page: pdfplumber page object
            
        Returns:
            Tuple of (left_column_lines, right_column_lines)
        """
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False
        )
        
        if not words:
            return [], []
        
        # Determine column boundary (middle of page)
        page_width = page.width
        mid_x = page_width / 2
        
        # Separate words into left and right columns
        left_words = [w for w in words if w['x0'] < mid_x]
        right_words = [w for w in words if w['x0'] >= mid_x]
        
        # Convert each column to lines
        left_lines = self._words_to_lines(left_words)
        right_lines = self._words_to_lines(right_words)
        
        return left_lines, right_lines
    
    def _words_to_lines(self, words: List[Dict]) -> List[str]:
        """
        Converts list of words to lines based on vertical position.
        
        Args:
            words: List of word dictionaries from pdfplumber
            
        Returns:
            List of text lines
        """
        if not words:
            return []
        
        # Group words by y-position (vertical)
        lines_dict = {}
        for word in words:
            y_pos = round(word['top'], 1)
            
            if y_pos not in lines_dict:
                lines_dict[y_pos] = []
            lines_dict[y_pos].append(word)
        
        # Sort words within each line by x position and join
        lines = []
        for y_pos in sorted(lines_dict.keys()):
            words_in_line = sorted(lines_dict[y_pos], key=lambda w: w['x0'])
            line_text = ' '.join(w['text'] for w in words_in_line)
            lines.append(line_text.strip())
        
        return lines
    
    def extract_occupations_from_column(self, lines: List[str]) -> List[Occupation]:
        """
        Extracts occupations from a single column of text.
        
        Args:
            lines: List of text lines from one column
            
        Returns:
            List of extracted Occupation objects
        """
        occupations = []
        current_occ: Optional[Occupation] = None
        description_lines = []
        in_metadata = False
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            # Skip page numbers
            if re.match(r'^\d+$', line) and len(line) <= 3:
                continue
            
            # Detect metadata sections
            if self.is_metadata_section(line):
                in_metadata = True
                # Save current occupation before entering metadata
                if current_occ and description_lines:
                    current_occ.description = ' '.join(description_lines).strip()
                    if current_occ.is_valid():
                        occupations.append(current_occ)
                    current_occ = None
                    description_lines = []
                continue
            
            # Skip lines while in metadata
            if in_metadata:
                # Exit metadata when we see a new valid code
                first_word = line.split()[0] if line.split() else ""
                if self.is_valid_nco_code(first_word):
                    in_metadata = False
                else:
                    continue
            
            # Skip header lines
            if self.is_header_line(line):
                continue
            
            # Try to detect new occupation (starts with 4-digit code)
            first_word = line.split()[0] if line.split() else ""
            
            if self.is_valid_nco_code(first_word):
                # Save previous occupation
                if current_occ and description_lines:
                    current_occ.description = ' '.join(description_lines).strip()
                    if current_occ.is_valid():
                        occupations.append(current_occ)
                
                # Start new occupation
                code = first_word
                title_parts = line.split()[1:]
                title = ' '.join(title_parts).strip()
                
                # Clean title
                title = re.sub(r'\s*\(.*?ISCO.*?\)', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s*ISCO.*$', '', title, flags=re.IGNORECASE)
                title = title.strip(';,. ')
                
                # Validate title
                if not title or len(title) < 3:
                    current_occ = None
                    description_lines = []
                    continue
                
                current_occ = Occupation(
                    nco_code=code,
                    title=title,
                    description=""
                )
                description_lines = []
                
            elif current_occ:
                # Check if description should stop
                if self.should_stop_description(line):
                    # Finalize current occupation
                    if description_lines:
                        current_occ.description = ' '.join(description_lines).strip()
                        if current_occ.is_valid():
                            occupations.append(current_occ)
                    current_occ = None
                    description_lines = []
                    in_metadata = True
                    continue
                
                # Add to description if not metadata/header
                if not self.is_metadata_section(line) and not self.is_header_line(line):
                    description_lines.append(line)
        
        # Don't forget last occupation
        if current_occ and description_lines:
            current_occ.description = ' '.join(description_lines).strip()
            if current_occ.is_valid():
                occupations.append(current_occ)
        
        return occupations
    
    def extract_from_pdf(self, pdf_path: Path) -> List[Occupation]:
        """
        Extracts all occupations from a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of extracted Occupation objects
        """
        all_occupations = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Skip cover pages (usually first 5-10 pages)
                if page_num < 5:
                    continue
                
                # Split page into columns
                left_lines, right_lines = self.split_into_columns(page)
                
                # Extract from left column first, then right column
                left_occs = self.extract_occupations_from_column(left_lines)
                right_occs = self.extract_occupations_from_column(right_lines)
                
                all_occupations.extend(left_occs)
                all_occupations.extend(right_occs)
                
                if page_num % 50 == 0:
                    print(f"  Processed {page_num} pages, found {len(all_occupations)} occupations so far...")
        
        return all_occupations
    
    def extract_all(self) -> List[Occupation]:
        """Extracts occupations from all configured PDF files."""
        all_occupations = []
        
        for pdf_path in self.pdf_paths:
            print(f"\nProcessing: {pdf_path.name}")
            occupations = self.extract_from_pdf(pdf_path)
            all_occupations.extend(occupations)
            print(f"  Extracted: {len(occupations)} occupations")
        
        self.occupations = all_occupations
        return all_occupations
    
    def deduplicate(self) -> List[Occupation]:
        """Removes duplicate occupation entries based on NCO code."""
        seen_codes = set()
        unique_occupations = []
        
        for occ in self.occupations:
            if occ.nco_code not in seen_codes:
                seen_codes.add(occ.nco_code)
                unique_occupations.append(occ)
        
        self.occupations = unique_occupations
        return unique_occupations
    
    def clean_text(self, text: str) -> str:
        """Cleans extracted text by normalizing whitespace."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove PDF artifacts
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
        
        # Remove page number artifacts
        text = re.sub(r'\bPage\s+\d+\b', '', text, flags=re.IGNORECASE)
        
        # Remove "Code XXXX Title" artifacts
        text = re.sub(r'\bCode\s+\d{4}\s+Title\b', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def export_to_csv(self, output_path: str):
        """Exports extracted occupations to CSV file."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['nco_code', 'title', 'description'])
            
            for occ in self.occupations:
                writer.writerow([
                    occ.nco_code,
                    self.clean_text(occ.title),
                    self.clean_text(occ.description)
                ])
        
        print(f"\n{'='*80}")
        print(f"✓ Exported {len(self.occupations)} occupations to: {output_path}")
        print('='*80)
    
    def print_statistics(self):
        """Prints extraction statistics for validation."""
        print("\n" + "="*80)
        print("EXTRACTION STATISTICS")
        print("="*80)
        print(f"Total occupations extracted: {len(self.occupations)}")
        
        if self.occupations:
            # Division distribution
            divisions = {}
            for occ in self.occupations:
                div = occ.nco_code[0]
                divisions[div] = divisions.get(div, 0) + 1
            
            print("\nOccupations per Division:")
            for div in sorted(divisions.keys()):
                print(f"  Division {div}: {divisions[div]:4d} occupations")
            
            # Description length statistics
            desc_lengths = [len(occ.description) for occ in self.occupations]
            avg_length = sum(desc_lengths) / len(desc_lengths)
            min_length = min(desc_lengths)
            max_length = max(desc_lengths)
            
            print(f"\nDescription Statistics:")
            print(f"  Average length: {avg_length:.0f} characters")
            print(f"  Min length: {min_length} characters")
            print(f"  Max length: {max_length} characters")
            
            # Sample occupations
            print("\nSample Occupations (first 3):")
            for occ in self.occupations[:3]:
                print(f"\n  Code: {occ.nco_code}")
                print(f"  Title: {occ.title}")
                print(f"  Desc: {occ.description[:200]}...")
        
        print("="*80)


def main():
    """Main execution function."""
    
    # CONFIGURATION: Update these paths
    PDF_FILES = [
        "data/raw/NCO_2015_Vol_II_Part1.pdf",
        "data/raw/NCO_2015_Vol_II_Part2.pdf"
    ]
    
    OUTPUT_CSV = "data/nco.csv"
    
    print("NCO-2015 Occupation Data Extractor v2.0")
    print("Two-Column Layout Handler")
    print("="*80)
    
    # Validate input files
    for pdf_file in PDF_FILES:
        if not Path(pdf_file).exists():
            print(f"ERROR: File not found: {pdf_file}")
            print("\nPlease update PDF_FILES with correct paths.")
            return
    
    # Extract occupations
    extractor = NCOExtractor(PDF_FILES)
    extractor.extract_all()
    
    # Deduplicate
    print("\nDeduplicating...")
    extractor.deduplicate()
    
    # Export to CSV
    extractor.export_to_csv(OUTPUT_CSV)
    
    # Print statistics
    extractor.print_statistics()
    
    print("\n" + "="*80)
    print("VALIDATION CHECKLIST")
    print("="*80)
    print(f"✓ Expected range: 900-2500 occupations")
    print(f"✓ Actual extracted: {len(extractor.occupations)}")
    print(f"✓ All codes 4 digits: {all(len(o.nco_code) == 4 for o in extractor.occupations)}")
    print(f"✓ No year codes: {'2015' not in [o.nco_code for o in extractor.occupations]}")
    print(f"✓ All start with 1-9: {all(o.nco_code[0] != '0' for o in extractor.occupations)}")
    
    # Quality checks
    short_descs = sum(1 for o in extractor.occupations if len(o.description) < 50)
    print(f"⚠ Descriptions < 50 chars: {short_descs}")
    
    print("="*80)
    

if __name__ == "__main__":
    main()