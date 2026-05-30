import re

class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.col})"

# Keywords list
KEYWORDS = {
    'int', 'char', 'void', 'if', 'else', 'while', 'for', 'do', 
    'break', 'continue', 'return', 'switch', 'case', 'default'
}

class LexicalError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"Lexical error at line {line}, col {col}: {message}")
        self.line = line
        self.col = col
        self.message = message

def strip_comments(source):
    """
    Strips block and line comments while preserving line breaks to keep line numbers accurate.
    """
    # Replace block comments /* ... */ with spaces/newlines
    def repl_block(match):
        return re.sub(r'[^\n]', ' ', match.group(0))
    
    # Replace line comments // ... with spaces (up to newline)
    def repl_line(match):
        return re.sub(r'[^\n]', ' ', match.group(0))

    # Strip block comments first
    source = re.sub(r'/\*.*?\*/', repl_block, source, flags=re.DOTALL)
    # Strip line comments
    source = re.sub(r'//[^\n]*', repl_line, source)
    return source

class Lexer:
    def __init__(self, source_code):
        self.source = strip_comments(source_code)
        self.position = 0
        self.line = 1
        self.col = 1
        self.length = len(self.source)
        self.macros = {}  # NAME -> raw string value (e.g. '8' or '100')
        self.tokens = []
        self.token_idx = 0
        
        self._extract_macros()
        self._tokenize()

    def _extract_macros(self):
        """
        Scan the source for `#define NAME VALUE` and store them in self.macros,
        then replace the `#define ...` directive with blank spaces/newlines.
        """
        # Search for lines starting with #define
        # Pattern: ^[ \t]*#[ \t]*define[ \t]+([a-zA-Z_][a-zA-Z0-9_]*)[ \t]+([^\n]+)
        # We need to do this line by line or with a regex that handles multiline.
        lines = self.source.split('\n')
        for i, line in enumerate(lines):
            match = re.match(r'^[ \t]*#[ \t]*define[ \t]+([a-zA-Z_][a-zA-Z0-9_]*)[ \t]+([^\r\n]+)', line)
            if match:
                macro_name = match.group(1)
                macro_val = match.group(2).strip()
                # Remove comments if any remain in macro_val (normally already stripped)
                self.macros[macro_name] = macro_val
                # Replace the line with spaces to preserve line numbers
                lines[i] = ' ' * len(line)
        self.source = '\n'.join(lines)
        self.length = len(self.source)

    def _peek(self, offset=0):
        pos = self.position + offset
        if pos >= self.length:
            return None
        return self.source[pos]

    def _advance(self):
        ch = self._peek()
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.position += 1
        return ch

    def _tokenize(self):
        while self.position < self.length:
            ch = self._peek()

            if ch is None:
                break

            # Whitespace
            if ch.isspace():
                self._advance()
                continue

            # Hexadecimal constant (must peek 0x/0X)
            if ch == '0' and (self._peek(1) == 'x' or self._peek(1) == 'X'):
                start_line, start_col = self.line, self.col
                self._advance() # '0'
                self._advance() # 'x'
                hex_str = ""
                while True:
                    next_ch = self._peek()
                    if next_ch is not None and next_ch.lower() in '0123456789abcdef':
                        hex_str += self._advance()
                    else:
                        break
                if not hex_str:
                    raise LexicalError("Invalid hexadecimal constant", start_line, start_col)
                val = int(hex_str, 16)
                self.tokens.append(Token('HEX', val, start_line, start_col))
                continue

            # Decimal Number
            if ch.isdigit():
                start_line, start_col = self.line, self.col
                num_str = ""
                while True:
                    next_ch = self._peek()
                    if next_ch is not None and next_ch.isdigit():
                        num_str += self._advance()
                    else:
                        break
                self.tokens.append(Token('INT_CONST', int(num_str), start_line, start_col))
                continue

            # Character Constant
            if ch == "'":
                start_line, start_col = self.line, self.col
                self._advance() # quote
                val = self._parse_char_literal(start_line, start_col)
                self.tokens.append(Token('CHAR_CONST', val, start_line, start_col))
                continue

            # String Constant
            if ch == '"':
                start_line, start_col = self.line, self.col
                self._advance() # quote
                val = self._parse_string_literal(start_line, start_col)
                self.tokens.append(Token('STR_CONST', val, start_line, start_col))
                continue

            # Identifiers & Keywords
            if ch.isalpha() or ch == '_':
                start_line, start_col = self.line, self.col
                ident_str = ""
                while True:
                    next_ch = self._peek()
                    if next_ch is not None and (next_ch.isalnum() or next_ch == '_'):
                        ident_str += self._advance()
                    else:
                        break
                
                # Check macro replacement
                if ident_str in self.macros:
                    # Tokenize the macro value recursively
                    macro_lexer = Lexer(self.macros[ident_str])
                    # Update macro token lines/cols to match replacement point
                    # Discard the trailing EOF token of the macro lexer
                    macro_tokens = macro_lexer.tokens[:-1] if macro_lexer.tokens and macro_lexer.tokens[-1].type == 'EOF' else macro_lexer.tokens
                    for t in macro_tokens:
                        t.line = start_line
                        t.col = start_col
                    self.tokens.extend(macro_tokens)
                elif ident_str in KEYWORDS:
                    self.tokens.append(Token(ident_str.upper(), ident_str, start_line, start_col))
                else:
                    self.tokens.append(Token('IDENT', ident_str, start_line, start_col))
                continue

            # Multi-character Operators (2-char)
            two_chars = {
                '==': 'EQ', '!=': 'NE', '<=': 'LE', '>=': 'GE',
                '&&': 'AND', '||': 'OR', '<<': 'SHL', '>>': 'SHR',
                '+=': 'ADD_ASSIGN', '-=': 'SUB_ASSIGN', '*=': 'MUL_ASSIGN',
                '/=': 'DIV_ASSIGN', '%=': 'MOD_ASSIGN', '++': 'INC', '--': 'DEC'
            }
            peek_two = ch + (self._peek(1) or '')
            if peek_two in two_chars:
                start_line, start_col = self.line, self.col
                self._advance()
                self._advance()
                self.tokens.append(Token(two_chars[peek_two], peek_two, start_line, start_col))
                continue

            # Single-character Operators & Punctuation
            single_chars = {
                '+': 'PLUS', '-': 'MINUS', '*': 'MUL', '/': 'DIV', '%': 'MOD',
                '<': 'LT', '>': 'GT', '=': 'ASSIGN', '&': 'AMP', '|': 'BAR',
                '^': 'CARET', '~': 'TILDE', '!': 'EXCL', ';': 'SEMI', ',': 'COMMA',
                '(': 'LPAREN', ')': 'RPAREN', '{': 'LBRACE', '}': 'RBRACE',
                '[': 'LBRACKET', ']': 'RBRACKET', ':': 'COLON'
            }
            if ch in single_chars:
                start_line, start_col = self.line, self.col
                self._advance()
                self.tokens.append(Token(single_chars[ch], ch, start_line, start_col))
                continue

            # Unrecognized character
            raise LexicalError(f"Unexpected character '{ch}'", self.line, self.col)

        # Append EOF Token
        self.tokens.append(Token('EOF', None, self.line, self.col))

    def _parse_char_literal(self, start_line, start_col):
        ch = self._peek()
        if ch is None:
            raise LexicalError("Unterminated character literal", start_line, start_col)
        
        val = 0
        if ch == '\\':
            self._advance()
            esc = self._peek()
            if esc is None:
                raise LexicalError("Unterminated character literal after backslash", start_line, start_col)
            
            escape_map = {
                'n': ord('\n'),
                't': ord('\t'),
                '0': 0,
                '\\': ord('\\'),
                "'": ord("'"),
                '"': ord('"'),
                'r': ord('\r'),
                'b': ord('\b'),
                'f': ord('\f'),
                'a': ord('\a'),
                'v': ord('\v')
            }
            if esc in escape_map:
                val = escape_map[esc]
                self._advance()
            else:
                # Default behavior for unknown escape: just treat the char as itself
                val = ord(esc)
                self._advance()
        else:
            val = ord(ch)
            self._advance()
            
        if self._peek() != "'":
            raise LexicalError("Character literal must be single character only", start_line, start_col)
        self._advance() # closing quote
        return val

    def _parse_string_literal(self, start_line, start_col):
        s = ""
        while True:
            ch = self._peek()
            if ch is None:
                raise LexicalError("Unterminated string literal", start_line, start_col)
            if ch == '"':
                self._advance()
                break
            if ch == '\\':
                self._advance()
                esc = self._peek()
                if esc is None:
                    raise LexicalError("Unterminated string literal after backslash", start_line, start_col)
                escape_map = {
                    'n': '\n',
                    't': '\t',
                    '0': '\0',
                    '\\': '\\',
                    "'": "'",
                    '"': '"',
                    'r': '\r',
                    'b': '\b',
                    'f': '\f',
                    'a': '\a',
                    'v': '\v'
                }
                if esc in escape_map:
                    s += escape_map[esc]
                    self._advance()
                else:
                    s += esc
                    self._advance()
            else:
                s += self._advance()
        return s

    def peek_token(self):
        if self.token_idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.token_idx]

    def consume_token(self):
        t = self.peek_token()
        self.token_idx += 1
        return t

    def match_token(self, expected_type):
        t = self.peek_token()
        if t.type == expected_type:
            return self.consume_token()
        return None
