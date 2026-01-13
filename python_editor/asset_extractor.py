import os
import re

# Supported extensions and their simple regex patterns
# This is a basic starting point.
PATTERNS = {
    'python': {
        'extensions': ['.py'],
        'patterns': [
            (r'^\s*class\s+(\w+)', 'Class'),
            (r'^\s*def\s+(\w+)', 'Function'),
            (r'^\s*([A-Z_][A-Z0-9_]*)\s*=', 'Variable'), # Mapping constant to Variable/Pink category for now, or distinct
            (r'^\s*#\s*region\s+(.+)', 'Region')
        ]
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'patterns': [
            # React Components (PascalCase functions)
            (r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Z]\w+)', 'Component'),
            (r'^\s*(?:export\s+)?(?:const|var|let)\s+([A-Z]\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w\d]+)\s*=>', 'Component'), # Arrow func component
            (r'^\s*class\s+(\w+)', 'Class'),
            (r'^\s*(?:async\s+)?function\s+([a-z]\w+)', 'Function'), # camelCase functions
            (r'^\s*(?:const|var|let)\s+([a-z]\w+)\s*=', 'Variable'),
            (r'^\s*//\s*#region\s+(.+)', 'Region')
        ]
    },
    'cpp': {
        'extensions': ['.cpp', '.c', '.h', '.hpp'],
        'patterns': [
            (r'^\s*class\s+(\w+)', 'Class'),
            (r'^\s*\w+\s+(\w+)\s*\(', 'Function'),
            (r'^\s*#pragma\s+region\s+(.+)', 'Region')
        ]
    },
    'html': {
         'extensions': ['.html', '.htm'],
         'patterns': [
             (r'<([a-zA-Z0-9-]+)(?:\s+[^>]*)?>', 'Component') # Treat tags as components
         ]
    },
    'java': {
        'extensions': ['.java'],
        'patterns': [
            (r'^\s*(?:public|private|protected)?\s*class\s+(\w+)', 'Class'),
            (r'^\s*(?:public|private|protected)?\s*(?:\w+\s+)+\s*(\w+)\s*\(', 'Function'),
            # Region syntax in Java is usually IDE specific, e.g. //region
             (r'^\s*//\s*region\s+(.+)', 'Region')
        ]
    },
    'csharp': {
        'extensions': ['.cs'],
        'patterns': [
            (r'^\s*(?:public|private|protected|internal)?\s*class\s+(\w+)', 'Class'),
            (r'^\s*(?:public|private|protected|internal)?\s*(?:\w+\s+)+\s*(\w+)\s*\(', 'Function'),
            (r'^\s*#region\s+(.+)', 'Region')
        ]
    },
    'php': {
        'extensions': ['.php'],
        'patterns': [
            (r'^\s*class\s+(\w+)', 'Class'),
            (r'^\s*function\s+(\w+)', 'Function'),
            (r'^\s*(\$\w+)\s*=', 'Variable'),
            (r'^\s*#\s*region\s+(.+)', 'Region')
        ]
    },
    'ruby': {
        'extensions': ['.rb'],
        'patterns': [
            (r'^\s*class\s+(\w+)', 'Class'),
            (r'^\s*def\s+(\w+)', 'Function'),
            (r'^\s*([A-Z]\w*)\s*=', 'Variable') # Constant
        ]
    },
     'go': {
        'extensions': ['.go'],
        'patterns': [
            (r'^\s*type\s+(\w+)\s+struct', 'Class'), 
            (r'^\s*func\s+(\w+)', 'Function')
        ]
    }
}

class CodeAsset:
    def __init__(self, name, asset_type, file_path, line_number):
        self.name = name
        self.asset_type = asset_type
        self.file_path = file_path
        self.line_number = line_number

    def __repr__(self):
        return f"[{self.asset_type}] {self.name} ({os.path.basename(self.file_path)})"

def get_language(filename):
    ext = os.path.splitext(filename)[1].lower()
    for lang, data in PATTERNS.items():
        if ext in data['extensions']:
            return lang, data
    return None, None

def extract_assets_from_file(file_path):
    assets = []
    lang, data = get_language(file_path)
    
    if not lang:
        return assets

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            for pattern, asset_type in data['patterns']:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    assets.append(CodeAsset(name, asset_type, file_path, i + 1))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return assets

def scan_project_assets(root_path):
    all_assets = []
    # Common directories to ignore
    IGNORED_DIRS = {
        'node_modules', 'venv', '.venv', 'env', '.env', 
        'dist', 'build', 'target', 'bin', 'obj', 
        '__pycache__', '.git', '.idea', '.vscode'
    }

    for root, dirs, files in os.walk(root_path):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]
        
        for file in files:
            file_path = os.path.join(root, file)
            # Optimization: Check extension before calling extract function
            # identifying if it's a known extension first
            ext = os.path.splitext(file)[1].lower()
            known_ext = False
            for data in PATTERNS.values():
                if ext in data['extensions']:
                    known_ext = True
                    break
            
            if known_ext:
                assets = extract_assets_from_file(file_path)
                all_assets.extend(assets)
            
    return all_assets
