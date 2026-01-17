import re
import os
import bisect
import tkinter as tk
from syntax_definitions import COLORS, LANGUAGES

class SyntaxHighlighter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.configure_tags()

    def configure_tags(self):
        """Configure the tags for syntax highlighting based on the color scheme."""
        for tag, color in COLORS.items():
            self.text_widget.tag_config(tag, foreground=color)

    def get_language_from_extension(self, file_path):
        """Determine the language based on the file extension."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        for lang, data in LANGUAGES.items():
            if ext in data['extensions']:
                return lang, data
        return None, None

    def highlight(self, content, file_path=""):
        """Apply syntax highlighting to the text widget."""
        # Remove existing tags
        for tag in COLORS.keys():
            self.text_widget.tag_remove(tag, "1.0", "end")

        lang_name, lang_data = self.get_language_from_extension(file_path)
        if not lang_data:
            return

        # self.text_widget.get("1.0", "end") matches 'content' usually, 
        # but we iterate over patterns and find matches in 'content' string
        # then map those matches to line.col in the text widget.
        
        # Helper to apply tag to a match object
        def apply_tag(tag, match):
            start = match.start()
            end = match.end()
            # Convert string index to tkinter 'line.col'
            # Note: This is computationally expensive for large files if done naively.
            # A better approach for Tkinter is to search line by line or use built-in search.
            # However, since we have the full content string, let's map indices.
            
            # Optimization: 
            # Tkinter text indices are "line_num.char_index" (1-based lines, 0-based chars)
            # We can calculate this from the content string if we know line breaks.
            pass

        # To avoid index mapping complexity and performance issues with mapping absolute indices 
        # to row.col, we will process line by line or using Tkinter's built-in search?
        # Using Tkinter's search for regex is possible but limited (Tcl regexp).
        # Python's re is more powerful. 
        
        # Strategy:
        # 1. Iterate over all regex patterns in the language definition.
        # 2. Find all matches in the content string.
        # 3. Convert match start/end to Tkinter indices.
        # 4. Apply tags.
        
        # Pre-calculate cumulative line lengths to quickly map index -> line.col
        lines = content.splitlines(keepends=True)
        line_offsets = [0]
        for line in lines:
            line_offsets.append(line_offsets[-1] + len(line))
            
        def get_index(offset):
            # Binary search could be used here but linear scan is okay for now or using bisect
            import bisect
            line_idx = bisect.bisect_right(line_offsets, offset) - 1
            col_idx = offset - line_offsets[line_idx]
            return f"{line_idx + 1}.{col_idx}"

        # Order of application matters: 
        # generally comments and strings should override keywords.
        # So we apply keywords first, then others, OR use priority.
        # But `tag_add` just adds a tag, multiple tags can exist.
        # `tag_raise` can preserve precedence.
        
        # Let's apply in this order:
        # 1. Keywords / Builtins / Constants (Matches whole words usually)
        # 2. Regex patterns (Numbers, Decorators, etc)
        # 3. Strings
        # 4. Comments (Highest priority usually covers everything inside)
        
        # 1. Word-based highlighting (Keywords, Builtins, Constants, Types, etc)
        word_categories = {
            'keyword': lang_data.get('keywords', []),
            'constant': lang_data.get('constants', []),
            'builtin': lang_data.get('builtins', []), # Map to 'function' or 'support'
            'type': lang_data.get('types', []),
            'function': [], # Hard to match exact function defs with just lists, regex pref.
            'self_args': lang_data.get('self_args', []),
            'sql_function': lang_data.get('functions', []), # For SQL
            'boolean': lang_data.get('constants', []), # reused
        }
        
        # Pre-compile word patterns for performance
        # \b(word1|word2|...)\b
        for category, words in word_categories.items():
            if not words: continue
            
            # Map category to specific color tag
            color_tag = category
            if category == 'builtin': color_tag = 'function' # approximate
            if category == 'self_args': color_tag = 'variable'
            if category == 'sql_function': color_tag = 'function'
            if category not in COLORS and color_tag not in COLORS: color_tag = 'keyword' # fallback

            escaped_words = [re.escape(w) for w in words]
            pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
            
            for match in re.finditer(pattern, content):
                 start_idx = get_index(match.start())
                 end_idx = get_index(match.end())
                 self.text_widget.tag_add(color_tag, start_idx, end_idx)

        # 2. Regex-based patterns (defined in LANGUAGES)
        # Categories that are lists of regex strings:
        regex_categories = [
            ('comment', lang_data.get('comments', [])),
            ('string', lang_data.get('strings', [])),
            ('number', lang_data.get('numbers', [])),
            ('decorator', lang_data.get('decorators', [])),
            ('preprocessor', lang_data.get('preprocessor', [])), # maps to keyword/control usually
            ('variable', lang_data.get('variables', [])), # PHP/Ruby vars
            ('tag', lang_data.get('tags', [])), # HTML
            ('attribute', lang_data.get('attributes', [])), # HTML
            ('selector', lang_data.get('selectors', [])), # CSS
            ('property', lang_data.get('properties', [])), # CSS
            ('header', lang_data.get('headers', [])), # MD
            ('bold', lang_data.get('bold', [])), # MD
            ('code', lang_data.get('code', [])), # MD
            ('link', lang_data.get('links', [])), # MD
            ('key', lang_data.get('keys', [])), # YAML/JSON
        ]

        for tag_name, patterns in regex_categories:
            if not patterns: continue
            
            final_tag = tag_name
            if tag_name == 'preprocessor': final_tag = 'keyword'
            if tag_name == 'header': final_tag = 'constant' # Distinct color
            if tag_name == 'link': final_tag = 'string'
            if tag_name == 'key': final_tag = 'variable'
            
            for pat in patterns:
                try:
                    for match in re.finditer(pat, content, re.MULTILINE):
                        start_idx = get_index(match.start())
                        end_idx = get_index(match.end())
                        self.text_widget.tag_add(final_tag, start_idx, end_idx)
                except re.error:
                    pass

        # Ensure comments and strings are on top
        self.text_widget.tag_raise('string')
        self.text_widget.tag_raise('comment')
