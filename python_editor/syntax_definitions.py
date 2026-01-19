
# VS Code Dark+ Color Scheme
COLORS = {
    'keyword':       '#C586C0',   # Magenta - control flow keywords
    'control':       '#C586C0',   # Magenta - control flow
    'constant':      '#569CD6',   # Blue - true, false, null
    'type':          '#4EC9B0',   # Cyan - types
    'function':      '#DCDCAA',   # Yellow - functions and methods
    'variable':      '#9CDCFE',   # Light Blue - variables
    'string':        '#CE9178',   # Orange - strings
    'number':        '#B5CEA8',   # Green - numbers
    'comment':       '#6A9955',   # Green dim - comments
    'operator':      '#D4D4D4',   # Light Gray - operators
    'punctuation':   '#D4D4D4',   # Light Gray - punctuation
    'decorator':     '#DCDCAA',   # Yellow - decorators
    'class':         '#4EC9B0',   # Cyan - class names
    'parameter':     '#9CDCFE',   # Light Blue - parameters
    'property':      '#9CDCFE',   # Light Blue - properties
    'tag':           '#569CD6',   # Blue - tags HTML
    'attribute':     '#9CDCFE',   # Light Blue - attributes HTML
    'selector':      '#D7BA7D',   # Gold - selectors CSS
    'default':       '#D4D4D4',   # Light Gray - default text
}

# Language Definitions
LANGUAGES = {
    'python': {
        'extensions': ['.py', '.pyw', '.pyi'],
        'keywords': [
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def', 'del', 
            'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 
            'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 
            'with', 'yield'
        ],
        'constants': ['True', 'False', 'None'],
        'builtins': [
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple', 'open', 
            'type', 'isinstance', 'hasattr', 'getattr', 'setattr', 'enumerate', 'zip', 'map', 
            'filter', 'sorted', 'reversed', 'sum', 'min', 'max', 'abs', 'round', 'super'
        ],
        'self_args': ['self', 'cls'],
        'comments': [r'#.*'],
        'strings': [r'""".*?"""', r"'''.*?'''", r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"],
        'numbers': [r'\b\d+\.?\d*\b', r'\b0x[0-9a-fA-F]+\b'],
        'decorators': [r'@\w+']
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'keywords': [
            'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 
            'do', 'else', 'export', 'extends', 'finally', 'for', 'function', 'if', 'import', 'in', 
            'instanceof', 'let', 'new', 'return', 'super', 'switch', 'this', 'throw', 'try', 
            'typeof', 'var', 'void', 'while', 'with', 'yield', 'async', 'await', 'static'
        ],
        'constants': ['true', 'false', 'null', 'undefined', 'NaN', 'Infinity'],
        'builtins': [
            'console', 'window', 'document', 'Array', 'Object', 'String', 'Number', 'Boolean', 
            'Function', 'Math', 'Date', 'JSON', 'Promise', 'Map', 'Set', 'Symbol', 'Error'
        ],
        'types': [
            'any', 'boolean', 'number', 'string', 'void', 'never', 'unknown', 'interface', 'type', 
            'enum', 'namespace', 'module', 'declare', 'readonly', 'public', 'private', 'protected', 
            'abstract', 'implements', 'as', 'is'
        ],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'", r'`(?:\\.|[^`\\])*`'],
        'numbers': [r'\b\d+\.?\d*\b', r'\b0x[0-9a-fA-F]+\b']
    },
    'cpp': {
        'extensions': ['.c', '.cpp', '.h', '.hpp', '.cc', '.hh'],
        'keywords': [
            'auto', 'break', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 
            'delete', 'do', 'double', 'else', 'enum', 'explicit', 'extern', 'float', 'for', 
            'friend', 'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new', 
            'operator', 'private', 'protected', 'public', 'register', 'return', 'short', 'signed', 
            'sizeof', 'static', 'struct', 'switch', 'template', 'this', 'throw', 'try', 'typedef', 
            'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'while', 
            'bool', 'true', 'false', 'nullptr'
        ],
        'preprocessor': [r'#\s*\w+'],
        'types': ['size_t', 'int8_t', 'int16_t', 'int32_t', 'int64_t', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t'],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"],
        'numbers': [r'\b\d+\.?\d*\b', r'\b0x[0-9a-fA-F]+\b']
    },
    'java': {
        'extensions': ['.java'],
        'keywords': [
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 
            'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 
            'finally', 'float', 'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int', 
            'interface', 'long', 'native', 'new', 'package', 'private', 'protected', 'public', 
            'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 
            'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while'
        ],
        'constants': ['true', 'false', 'null'],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"'],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'csharp': {
        'extensions': ['.cs'],
        'keywords': [
            'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch', 'char', 'checked', 
            'class', 'const', 'continue', 'decimal', 'default', 'delegate', 'do', 'double', 'else', 
            'enum', 'event', 'explicit', 'extern', 'false', 'finally', 'fixed', 'float', 'for', 
            'foreach', 'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal', 'is', 'lock', 
            'long', 'namespace', 'new', 'null', 'object', 'operator', 'out', 'override', 'params', 
            'private', 'protected', 'public', 'readonly', 'ref', 'return', 'sbyte', 'sealed', 
            'short', 'sizeof', 'stackalloc', 'static', 'string', 'struct', 'switch', 'this', 'throw', 
            'true', 'try', 'typeof', 'uint', 'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 
            'virtual', 'void', 'volatile', 'while', 'var', 'async', 'await'
        ],
        'linq': ['from', 'where', 'select', 'group', 'into', 'orderby', 'join', 'let', 'ascending', 'descending', 'on', 'equals', 'by'],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r'@"(?:""|[^"])*"'],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'php': {
        'extensions': ['.php'],
        'keywords': [
            'abstract', 'and', 'array', 'as', 'break', 'callable', 'case', 'catch', 'class', 'clone', 
            'const', 'continue', 'declare', 'default', 'die', 'do', 'echo', 'else', 'elseif', 'empty', 
            'enddeclare', 'endfor', 'endforeach', 'endif', 'endswitch', 'endwhile', 'eval', 'exit', 
            'extends', 'final', 'finally', 'fn', 'for', 'foreach', 'function', 'global', 'goto', 
            'if', 'implements', 'include', 'include_once', 'instanceof', 'insteadof', 'interface', 
            'isset', 'list', 'match', 'namespace', 'new', 'or', 'print', 'private', 'protected', 
            'public', 'require', 'require_once', 'return', 'static', 'switch', 'throw', 'trait', 
            'try', 'unset', 'use', 'var', 'while', 'xor', 'yield'
        ],
        'constants': ['true', 'false', 'null', 'TRUE', 'FALSE', 'NULL'],
        'builtins': ['__CLASS__', '__DIR__', '__FILE__', '__FUNCTION__', '__LINE__', '__METHOD__', '__NAMESPACE__', '__TRAIT__'],
        'variables': [r'\$\w+'],
        'comments': [r'//.*', r'#.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'ruby': {
        'extensions': ['.rb'],
        'keywords': [
            'alias', 'and', 'begin', 'break', 'case', 'class', 'def', 'defined?', 'do', 'else', 
            'elsif', 'end', 'ensure', 'false', 'for', 'if', 'in', 'module', 'next', 'nil', 'not', 
            'or', 'redo', 'rescue', 'retry', 'return', 'self', 'super', 'then', 'true', 'undef', 
            'unless', 'until', 'when', 'while', 'yield', 'require', 'require_relative', 'include', 
            'extend', 'attr_reader', 'attr_writer', 'attr_accessor', 'private', 'protected', 'public'
        ],
        'symbols': [r':\w+'],
        'variables': [r'@[a-zA-Z_]\w*', r'\$[a-zA-Z_]\w*'],
        'comments': [r'#.*'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'go': {
        'extensions': ['.go'],
        'keywords': [
            'break', 'case', 'chan', 'const', 'continue', 'default', 'defer', 'else', 'fallthrough', 
            'for', 'func', 'go', 'goto', 'if', 'import', 'interface', 'map', 'package', 'range', 
            'return', 'select', 'struct', 'switch', 'type', 'var'
        ],
        'types': [
            'bool', 'byte', 'complex64', 'complex128', 'error', 'float32', 'float64', 'int', 'int8', 
            'int16', 'int32', 'int64', 'rune', 'string', 'uint', 'uint8', 'uint16', 'uint32', 
            'uint64', 'uintptr'
        ],
        'constants': ['true', 'false', 'nil', 'iota'],
        'builtins': ['append', 'cap', 'close', 'complex', 'copy', 'delete', 'imag', 'len', 'make', 'new', 'panic', 'print', 'println', 'real', 'recover'],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r'`(?:\\.|[^`\\])*`'],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'html': {
        'extensions': ['.html', '.htm'],
        'tags': [r'</?\w+>?'],
        'attributes': [r'\s+\w+='],
        'comments': [r'<!--[\s\S]*?-->'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"]
    },
    'css': {
        'extensions': ['.css'],
        'selectors': [r'\.[\w-]+', r'#[\w-]+'],
        'properties': [r'[\w-]+:'],
        'units': [r'\d+(?:px|em|rem|%|vh|vw)'],
        'colors': [r'#[0-9a-fA-F]{3,6}', r'rgb\([^)]+\)', r'rgba\([^)]+\)'],
        'comments': [r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"]
    },
    'sql': {
        'extensions': ['.sql'],
        'keywords': [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 
            'TABLE', 'INDEX', 'VIEW', 'INTO', 'VALUES', 'SET', 'AND', 'OR', 'NOT', 'NULL', 'IS', 
            'IN', 'LIKE', 'BETWEEN', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AS', 
            'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'DISTINCT', 'UNION', 'ALL', 
            'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'PRIMARY', 'FOREIGN', 'KEY', 
            'REFERENCES', 'CONSTRAINT', 'DEFAULT', 'AUTO_INCREMENT', 'UNIQUE', 'CHECK'
        ],
        'functions': [
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'NULLIF', 'CAST', 'CONVERT', 
            'CONCAT', 'SUBSTRING', 'LENGTH', 'UPPER', 'LOWER', 'TRIM', 'NOW', 'DATE', 'YEAR', 
            'MONTH', 'DAY'
        ],
        'types': [
            'INT', 'INTEGER', 'VARCHAR', 'CHAR', 'TEXT', 'BOOLEAN', 'DATE', 'DATETIME', 
            'TIMESTAMP', 'DECIMAL', 'FLOAT', 'DOUBLE', 'BLOB'
        ],
        'comments': [r'--.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'rust': {
        'extensions': ['.rs'],
        'keywords': [
            'as', 'async', 'await', 'break', 'const', 'continue', 'crate', 'dyn', 'else', 'enum', 
            'extern', 'false', 'fn', 'for', 'if', 'impl', 'in', 'let', 'loop', 'match', 'mod', 
            'move', 'mut', 'pub', 'ref', 'return', 'self', 'Self', 'static', 'struct', 'super', 
            'trait', 'true', 'type', 'unsafe', 'use', 'where', 'while'
        ],
        'types': [
            'i8', 'i16', 'i32', 'i64', 'i128', 'isize', 'u8', 'u16', 'u32', 'u64', 'u128', 'usize', 
            'f32', 'f64', 'bool', 'char', 'str', 'String', 'Vec', 'Option', 'Result', 'Box', 'Rc', 
            'Arc', 'Cell', 'RefCell'
        ],
        'macros': [r'\w+!'],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"r(#*)\".*?\"\1"],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'swift': {
        'extensions': ['.swift'],
        'keywords': [
            'associatedtype', 'class', 'deinit', 'enum', 'extension', 'fileprivate', 'func', 
            'import', 'init', 'inout', 'internal', 'let', 'open', 'operator', 'private', 
            'protocol', 'public', 'rethrows', 'static', 'struct', 'subscript', 'typealias', 'var', 
            'break', 'case', 'continue', 'default', 'defer', 'do', 'else', 'fallthrough', 'for', 
            'guard', 'if', 'in', 'repeat', 'return', 'switch', 'where', 'while', 'as', 'catch', 
            'is', 'nil', 'throw', 'throws', 'try', 'false', 'true', 'self', 'Self', 'super'
        ],
        'types': [
            'Any', 'AnyObject', 'Bool', 'Character', 'Double', 'Float', 'Int', 'Int8', 'Int16', 
            'Int32', 'Int64', 'String', 'UInt', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'Void', 
            'Optional', 'Array', 'Dictionary', 'Set'
        ],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"'],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'kotlin': {
        'extensions': ['.kt', '.kts'],
        'keywords': [
            'abstract', 'actual', 'annotation', 'as', 'break', 'by', 'catch', 'class', 'companion', 
            'const', 'constructor', 'continue', 'crossinline', 'data', 'do', 'else', 'enum', 
            'expect', 'external', 'false', 'final', 'finally', 'for', 'fun', 'if', 'import', 'in', 
            'infix', 'init', 'inline', 'inner', 'interface', 'internal', 'is', 'it', 'lateinit', 
            'noinline', 'null', 'object', 'open', 'operator', 'out', 'override', 'package', 
            'private', 'protected', 'public', 'reified', 'return', 'sealed', 'super', 'suspend', 
            'this', 'throw', 'true', 'try', 'typealias', 'typeof', 'val', 'var', 'vararg', 'when', 
            'where', 'while'
        ],
        'types': [
            'Any', 'Boolean', 'Byte', 'Char', 'Double', 'Float', 'Int', 'Long', 'Nothing', 
            'Short', 'String', 'Unit'
        ],
        'comments': [r'//.*', r'/\*[\s\S]*?\*/'],
        'strings': [r'"(?:\\.|[^"\\])*"', r'""".*?"""'],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'bash': {
        'extensions': ['.sh', '.bash'],
        'keywords': [
            'if', 'then', 'else', 'elif', 'fi', 'case', 'esac', 'for', 'while', 'until', 'do', 
            'done', 'in', 'function', 'select', 'time', 'coproc', 'return', 'exit', 'break', 
            'continue', 'declare', 'local', 'export', 'readonly', 'unset', 'shift', 'source', 
            'alias', 'eval', 'exec', 'set', 'trap'
        ],
        'builtins': [
            'echo', 'printf', 'read', 'cd', 'pwd', 'ls', 'cat', 'grep', 'sed', 'awk', 'find', 
            'xargs', 'sort', 'uniq', 'wc', 'head', 'tail', 'cut', 'tr', 'test'
        ],
        'variables': [r'\$\w+', r'\${\w+}', r'\$[0-9@*#?]'],
        'comments': [r'#.*'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"]
    },
    'yaml': {
        'extensions': ['.yml', '.yaml'],
        'constants': ['true', 'false', 'yes', 'no', 'on', 'off', 'null', '~'],
        'keys': [r'[\w-]+:'],
        'comments': [r'#.*'],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"]
    },
    'json': {
        'extensions': ['.json'],
        'constants': ['true', 'false', 'null'],
        'keys': [r'"(?:\\.|[^"\\])*"\s*:', r"'(?:\\.|[^'\\])*'\s*:"],
        'strings': [r'"(?:\\.|[^"\\])*"', r"'(?:\\.|[^'\\])*'"],
        'numbers': [r'\b\d+\.?\d*\b']
    },
    'markdown': {
        'extensions': ['.md', '.markdown'],
        'headers': [r'^#+ .*'],
        'lists': [r'^\s*[-*+] .*', r'^\s*\d+\. .*'],
        'code': [r'`[^`]*`', r'```[\s\S]*?```'],
        'links': [r'\[.*?\]\(.*?\)'],
        'bold': [r'\*\*.*?\*\*', r'__.*?__'],
        'italic': [r'\*.*?\*', r'_.*?_']
    }
}
