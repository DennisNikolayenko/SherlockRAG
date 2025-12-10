#!/usr/bin/env python3
"""
Parse Complete Sherlock Holmes Canon
Splits the giant text file into individual stories with metadata
"""

import os                    # File operations
import re                    # Regular expressions
import json                  # Save metadata
from typing import List, Dict

# Story metadata (manually compiled from canon knowledge)
STORY_METADATA = {
    # Novels
    "A Study In Scarlet": {"year": 1887, "type": "novel", "collection": "Novels"},
    "The Sign of the Four": {"year": 1890, "type": "novel", "collection": "Novels"},
    "The Hound of the Baskervilles": {"year": 1902, "type": "novel", "collection": "Novels"},
    "The Valley Of Fear": {"year": 1915, "type": "novel", "collection": "Novels"},
    
    # Adventures of Sherlock Holmes (1892)
    "A Scandal in Bohemia": {"year": 1891, "type": "short_story", "collection": "Adventures"},
    "The Red-Headed League": {"year": 1891, "type": "short_story", "collection": "Adventures"},
    "A Case of Identity": {"year": 1891, "type": "short_story", "collection": "Adventures"},
    "The Boscombe Valley Mystery": {"year": 1891, "type": "short_story", "collection": "Adventures"},
    "The Five Orange Pips": {"year": 1891, "type": "short_story", "collection": "Adventures"},
    "The Man with the Twisted Lip": {"year": 1891, "type": "short_story", "collection": "Adventures"},
    "The Adventure of the Blue Carbuncle": {"year": 1892, "type": "short_story", "collection": "Adventures"},
    "The Adventure of the Speckled Band": {"year": 1892, "type": "short_story", "collection": "Adventures"},
    "The Adventure of the Engineer's Thumb": {"year": 1892, "type": "short_story", "collection": "Adventures"},
    "The Adventure of the Noble Bachelor": {"year": 1892, "type": "short_story", "collection": "Adventures"},
    "The Adventure of the Beryl Coronet": {"year": 1892, "type": "short_story", "collection": "Adventures"},
    "The Adventure of the Copper Beeches": {"year": 1892, "type": "short_story", "collection": "Adventures"},
    
    # Memoirs of Sherlock Holmes (1894)
    "Silver Blaze": {"year": 1892, "type": "short_story", "collection": "Memoirs"},
    "The Yellow Face": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Stock-Broker's Clerk": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The \"Gloria Scott\"": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Musgrave Ritual": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Reigate Squires": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Crooked Man": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Resident Patient": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Greek Interpreter": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Naval Treaty": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    "The Final Problem": {"year": 1893, "type": "short_story", "collection": "Memoirs"},
    
    # Return of Sherlock Holmes (1905)
    "The Adventure of the Empty House": {"year": 1903, "type": "short_story", "collection": "Return"},
    "The Adventure of the Norwood Builder": {"year": 1903, "type": "short_story", "collection": "Return"},
    "The Adventure of the Dancing Men": {"year": 1903, "type": "short_story", "collection": "Return"},
    "The Adventure of the Solitary Cyclist": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of the Priory School": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of Black Peter": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of Charles Augustus Milverton": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of the Six Napoleons": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of the Three Students": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of the Golden Pince-Nez": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of the Missing Three-Quarter": {"year": 1904, "type": "short_story", "collection": "Return"},
    "The Adventure of the Abbey Grange": {"year": 1905, "type": "short_story", "collection": "Return"},
    "The Adventure of the Second Stain": {"year": 1905, "type": "short_story", "collection": "Return"},
    
    # His Last Bow (1917)
    "The Adventure of Wisteria Lodge": {"year": 1908, "type": "short_story", "collection": "His Last Bow"},
    "The Adventure of the Cardboard Box": {"year": 1893, "type": "short_story", "collection": "His Last Bow"},
    "The Adventure of the Red Circle": {"year": 1911, "type": "short_story", "collection": "His Last Bow"},
    "The Adventure of the Bruce-Partington Plans": {"year": 1908, "type": "short_story", "collection": "His Last Bow"},
    "The Adventure of the Dying Detective": {"year": 1913, "type": "short_story", "collection": "His Last Bow"},
    "The Disappearance of Lady Frances Carfax": {"year": 1911, "type": "short_story", "collection": "His Last Bow"},
    "The Adventure of the Devil's Foot": {"year": 1910, "type": "short_story", "collection": "His Last Bow"},
    "His Last Bow": {"year": 1917, "type": "short_story", "collection": "His Last Bow"},
    "His Last Bow: The War Service of Sherlock Holmes": {"year": 1917, "type": "short_story", "collection": "His Last Bow"},
    
    # Case-Book of Sherlock Holmes (1927)
    "The Illustrious Client": {"year": 1924, "type": "short_story", "collection": "Case-Book"},
    "The Blanched Soldier": {"year": 1926, "type": "short_story", "collection": "Case-Book"},
    "The Adventure Of The Mazarin Stone": {"year": 1921, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Three Gables": {"year": 1926, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Sussex Vampire": {"year": 1924, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Three Garridebs": {"year": 1924, "type": "short_story", "collection": "Case-Book"},
    "The Problem of Thor Bridge": {"year": 1922, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Creeping Man": {"year": 1923, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Lion's Mane": {"year": 1926, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Veiled Lodger": {"year": 1927, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of Shoscombe Old Place": {"year": 1927, "type": "short_story", "collection": "Case-Book"},
    "The Adventure of the Retired Colourman": {"year": 1926, "type": "short_story", "collection": "Case-Book"},
}


def clean_text(text: str) -> str:
    """Clean up text (remove extra whitespace, fix formatting)."""
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines in a row
    text = re.sub(r' {2,}', ' ', text)       # Max 1 space in a row
    text = text.strip()                      # Remove leading/trailing whitespace
    return text


def normalize_title(title: str) -> str:
    """Normalize story title for matching."""
    # Remove "The Adventure of" prefix for matching
    normalized = title.strip()
    normalized = re.sub(r'^The Adventure [Oo]f [Tt]he ', '', normalized)
    normalized = re.sub(r'^The Adventure [Oo]f ', '', normalized)
    return normalized


def find_story_boundaries(text: str) -> List[Dict]:
    """
    Find story boundaries in the complete canon text.
    Returns list of stories with start/end positions and titles.
    """
    print("📖 Analyzing story structure...")
    
    stories = []
    
    # Find all story titles (they appear as large centered text)
    # Pattern: look for lines that are all caps or title case, surrounded by whitespace
    title_pattern = r'\n\s*([A-Z][A-Za-z\s\-\'",]+)\s*\n'
    
    # Known story titles from metadata
    known_titles = list(STORY_METADATA.keys())
    
    # Find positions of each known title
    for title in known_titles:
        # Try different variations of the title
        patterns = [
            title.upper(),                    # ALL CAPS
            title,                            # As-is
            title.replace("The Adventure of the ", "").replace("The Adventure of ", ""),  # Without prefix
        ]
        
        for pattern in patterns:
            # Escape special regex characters
            escaped = re.escape(pattern)
            # Find in text
            matches = list(re.finditer(f'\n\s*{escaped}\s*\n', text, re.IGNORECASE))
            
            if matches:
                # Use the first match (story title in table of contents appears first)
                # We want the SECOND occurrence (actual story start)
                if len(matches) >= 2:
                    match = matches[1]  # Second occurrence (after TOC)
                else:
                    match = matches[0]  # Fallback to first if only one
                
                stories.append({
                    'title': title,
                    'start': match.start(),
                    'normalized_title': normalize_title(title)
                })
                break  # Found it, move to next title
    
    # Sort by position in text
    stories.sort(key=lambda x: x['start'])
    
    # Set end positions (start of next story)
    for i in range(len(stories) - 1):
        stories[i]['end'] = stories[i + 1]['start']
    
    # Last story goes to end of file
    if stories:
        stories[-1]['end'] = len(text)
    
    print(f"   Found {len(stories)} stories")
    return stories


def extract_stories(input_file: str, output_dir: str) -> List[Dict]:
    """
    Extract individual stories from the complete canon.
    
    Args:
        input_file: Path to complete canon text file
        output_dir: Where to save individual story files
        
    Returns:
        List of story metadata
    """
    print(f"\n📚 Extracting stories from: {input_file}")
    print("=" * 70)
    
    # Read the complete file
    print("📖 Reading complete canon...")
    with open(input_file, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"   {len(full_text):,} characters total")
    print(f"   ~{len(full_text.split()):,} words total\n")
    
    # Find story boundaries
    story_boundaries = find_story_boundaries(full_text)
    
    if not story_boundaries:
        print("❌ Could not find story boundaries!")
        return []
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract each story
    extracted_stories = []
    
    for i, story_info in enumerate(story_boundaries, 1):
        title = story_info['title']
        start = story_info['start']
        end = story_info['end']
        
        # Extract text
        story_text = full_text[start:end]
        story_text = clean_text(story_text)
        
        # Get metadata
        metadata = STORY_METADATA.get(title, {
            "year": None,
            "type": "unknown",
            "collection": "Unknown"
        })
        
        # Create filename (sanitize title)
        filename = title.replace(' ', '_').replace('"', '').replace('/', '_')
        filename = f"{i:02d}_{filename}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Save story
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(story_text)
        
        word_count = len(story_text.split())
        
        print(f"✅ {i:2d}. {title[:50]:<50} ({word_count:>6,} words)")
        
        # Store metadata
        extracted_stories.append({
            'id': i,
            'title': title,
            'filename': filename,
            'year': metadata['year'],
            'type': metadata['type'],
            'collection': metadata['collection'],
            'word_count': word_count,
            'char_count': len(story_text)
        })
    
    print("\n" + "=" * 70)
    print(f"✅ Extracted {len(extracted_stories)} stories!")
    
    return extracted_stories


def save_metadata(stories: List[Dict], output_file: str):
    """Save story metadata to JSON file."""
    print(f"\n💾 Saving metadata to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2)
    
    print(f"   ✅ Metadata saved!")


def print_statistics(stories: List[Dict]):
    """Print statistics about the extracted stories."""
    print(f"\n📊 Statistics:")
    print("=" * 70)
    
    # By type
    novels = [s for s in stories if s['type'] == 'novel']
    short_stories = [s for s in stories if s['type'] == 'short_story']
    
    print(f"   Novels: {len(novels)}")
    print(f"   Short Stories: {len(short_stories)}")
    print(f"   Total: {len(stories)}")
    
    # By collection
    collections = {}
    for story in stories:
        col = story['collection']
        collections[col] = collections.get(col, 0) + 1
    
    print(f"\n   By Collection:")
    for collection, count in sorted(collections.items()):
        print(f"      {collection}: {count}")
    
    # Word counts
    total_words = sum(s['word_count'] for s in stories)
    avg_words = total_words // len(stories)
    
    print(f"\n   Total Words: {total_words:,}")
    print(f"   Average per Story: {avg_words:,}")
    print(f"   Shortest: {min(s['word_count'] for s in stories):,} words")
    print(f"   Longest: {max(s['word_count'] for s in stories):,} words")
    
    print("=" * 70)


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("🔍 SHERLOCK HOLMES STORY PARSER")
    print("=" * 70)
    
    # Paths
    input_file = "data/raw/sherlock_complete.txt"
    output_dir = "data/processed/stories"
    metadata_file = "data/processed/stories_metadata.json"
    
    # Check input exists
    if not os.path.exists(input_file):
        print(f"\n❌ Error: Input file not found: {input_file}")
        print(f"   Please download the complete canon first!")
        return
    
    # Extract stories
    stories = extract_stories(input_file, output_dir)
    
    if not stories:
        print("\n❌ Failed to extract stories!")
        return
    
    # Save metadata
    save_metadata(stories, metadata_file)
    
    # Print statistics
    print_statistics(stories)
    
    print(f"\n🎉 SUCCESS!")
    print(f"   📁 Stories saved to: {output_dir}/")
    print(f"   📄 Metadata saved to: {metadata_file}")
    print(f"\n🔜 Next: Run build_index.py to create vector database!")


if __name__ == "__main__":
    main()