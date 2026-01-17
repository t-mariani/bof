import os
import hashlib
import json
import csv
from rich.console import Console 

# Initialize global console
console = Console()

BOF_DIR = ".bof"
CONTENT_DIR = "content"
STRUCTURE_FILE = "structure.csv"
INDEX_FILE = "index.json"

def get_sha1(filepath):
    """Calculates SHA1 of a file in chunks to handle large files"""
    sha1 = hashlib.sha1()
    try:
        with open(filepath, 'rb') as f:
            while True:
                # 64 Ko chunks 
                data = f.read(65536)
                if not data:
                    break
                # feed data to sha1, process incrementaly 
                sha1.update(data)
        return sha1.hexdigest()
    except (OSError, PermissionError):
        return None

def find_bof_root(start_path):
    """Searches for .bof in current or parent directories"""
    current = os.path.abspath(start_path)
    while True:
        if os.path.isdir(os.path.join(current, BOF_DIR)):
            return current
        parent = os.path.dirname(current)
        if parent == current: # Reached root
            return None
        current = parent

def load_index_metadata(bof_path):
    """Loads the index.json data"""
    try:
        with open(os.path.join(bof_path, BOF_DIR, INDEX_FILE), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def load_structure(bof_path):
    """Loads structure.csv into a dictionary {filepath: {sha1, mtime}}."""
    data = {}
    csv_path = os.path.join(bof_path, BOF_DIR, STRUCTURE_FILE)
    if not os.path.exists(csv_path):
        return data
        
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['filepath']] = {
                'sha1': row['sha1'],
                'mtime': float(row['mtime'])
            }
    return data