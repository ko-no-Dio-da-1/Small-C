class ASTNode:
    pass

class ProgramNode(ASTNode):
    def __init__(self, declarations):
        self.declarations = declarations  # List of VarDeclNode or FuncDefNode

class VarDeclNode(ASTNode):
    def __init__(self, type_name, name, is_pointer, array_size, init_expr, line):
        self.type_name = type_name
        self.name = name
        self.is_pointer = is_pointer
        self.array_size = array_size  # None if not array, integer if array
        self.init_expr = init_expr    # ASTNode or None
        self.line = line

    def __repr__(self):
        arr_str = f"[{self.array_size}]" if self.array_size is not None else ""
        ptr_str = "*" if self.is_pointer else ""
        init_str = f" = {self.init_expr}" if self.init_expr else ""
        return f"VarDecl({self.type_name} {ptr_str}{self.name}{arr_str}{init_str})"

class FuncDefNode(ASTNode):
    def __init__(self, return_type, name, is_pointer, params, decls, body, line):
        self.return_type = return_type
        self.name = name
        self.is_pointer = is_pointer
        self.params = params          # List of ParamDeclNode
        self.decls = decls            # List of VarDeclNode (local declarations)
        self.body = body              # List of ASTNode (statements)
        self.line = line

    def __repr__(self):
        ptr_str = "*" if self.is_pointer else ""
        return f"FuncDef({self.return_type} {ptr_str}{self.name}(...), decls={self.decls}, body_len={len(self.body)})"

class ParamDeclNode(ASTNode):
    def __init__(self, type_name, name, is_pointer, line):
        self.type_name = type_name
        self.name = name
        self.is_pointer = is_pointer
        self.line = line

    def __repr__(self):
        ptr_str = "*" if self.is_pointer else ""
        return f"ParamDecl({self.type_name} {ptr_str}{self.name})"

class BlockNode(ASTNode):
    def __init__(self, statements, line):
        self.statements = statements
        self.line = line

class IfNode(ASTNode):
    def __init__(self, cond, then_branch, else_branch, line):
        self.cond = cond
        self.then_branch = then_branch
        self.else_branch = else_branch # ASTNode or None
        self.line = line

class WhileNode(ASTNode):
    def __init__(self, cond, body, line):
        self.cond = cond
        self.body = body              # ASTNode
        self.line = line

class ForNode(ASTNode):
    def __init__(self, init, cond, step, body, line):
        self.init = init              # ASTNode or None (e.g. AssignNode)
        self.cond = cond              # ASTNode or None
        self.step = step              # ASTNode or None
        self.body = body              # ASTNode
        self.line = line

class DoWhileNode(ASTNode):
    def __init__(self, body, cond, line):
        self.body = body              # ASTNode
        self.cond = cond              # ASTNode
        self.line = line

class BreakNode(ASTNode):
    def __init__(self, line):
        self.line = line

class ContinueNode(ASTNode):
    def __init__(self, line):
        self.line = line

class ReturnNode(ASTNode):
    def __init__(self, expr, line):
        self.expr = expr              # ASTNode or None
        self.line = line

class SwitchNode(ASTNode):
    def __init__(self, expr, cases, default_case, line):
        self.expr = expr              # ASTNode
        self.cases = cases            # List of tuples: (case_value_int, statement_list)
        self.default_case = default_case # List of ASTNode or None
        self.line = line

class AssignNode(ASTNode):
    def __init__(self, left, op, right, line):
        self.left = left              # ASTNode (VariableNode, DereferenceNode, ArrayAccessNode)
        self.op = op                  # 'ASSIGN', 'ADD_ASSIGN', etc.
        self.right = right            # ASTNode
        self.line = line

    def __repr__(self):
        return f"Assign({self.left} {self.op} {self.right})"

class BinaryOpNode(ASTNode):
    def __init__(self, op, left, right, line):
        self.op = op                  # 'PLUS', 'MINUS', 'EQ', 'AND', etc.
        self.left = left
        self.right = right
        self.line = line

    def __repr__(self):
        return f"BinaryOp({self.op}, {self.left}, {self.right})"

class UnaryOpNode(ASTNode):
    def __init__(self, op, expr, line):
        self.op = op                  # 'MINUS', 'EXCL' (!), 'TILDE' (~), 'INC' (++), 'DEC' (--)
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"UnaryOp({self.op}, {self.expr})"

class AddressOfNode(ASTNode):
    def __init__(self, expr, line):
        self.expr = expr              # ASTNode
        self.line = line

class DereferenceNode(ASTNode):
    def __init__(self, expr, line):
        self.expr = expr              # ASTNode
        self.line = line

class ArrayAccessNode(ASTNode):
    def __init__(self, array_expr, index_expr, line):
        self.array_expr = array_expr
        self.index_expr = index_expr
        self.line = line

    def __repr__(self):
        return f"ArrayAccess({self.array_expr}[{self.index_expr}])"

class FuncCallNode(ASTNode):
    def __init__(self, name_expr, args, line):
        self.name_expr = name_expr    # Normally VariableNode(name)
        self.args = args              # List of ASTNode
        self.line = line

    def __repr__(self):
        return f"FuncCall({self.name_expr}, args={self.args})"

class VariableNode(ASTNode):
    def __init__(self, name, line):
        self.name = name
        self.line = line

    def __repr__(self):
        return f"Var({self.name})"

class LiteralNode(ASTNode):
    def __init__(self, value, type_, line):
        self.value = value            # Python value (int, string, or char ASCII)
        self.type = type_              # 'int', 'char', 'string'
        self.line = line

    def __repr__(self):
        return f"Literal({repr(self.value)}, type={self.type})"


class SyntaxError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"Syntax error at line {line}, col {col}: {message}")
        self.line = line
        self.col = col
        self.message = message


# Expression operator precedence climbing mapping
PRECEDENCE = {
    'ASSIGN': 1, 'ADD_ASSIGN': 1, 'SUB_ASSIGN': 1, 'MUL_ASSIGN': 1, 'DIV_ASSIGN': 1, 'MOD_ASSIGN': 1,
    'OR': 2,
    'AND': 3,
    'BAR': 4,      # |
    'CARET': 5,    # ^
    'AMP': 6,      # &
    'EQ': 7, 'NE': 7,
    'LT': 8, 'LE': 8, 'GT': 8, 'GE': 8,
    'SHL': 9, 'SHR': 9,
    'PLUS': 10, 'MINUS': 10,
    'MUL': 11, 'DIV': 11, 'MOD': 11,
    'LPAREN': 12,  # function call
    'LBRACKET': 12, # array access
}

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

    def _error(self, message):
        t = self.lexer.peek_token()
        raise SyntaxError(message, t.line, t.col)

    def _match(self, expected_type):
        t = self.lexer.match_token(expected_type)
        if not t:
            self._error(f"Expected token of type {expected_type}, got {self.lexer.peek_token().type}")
        return t

    def parse(self):
        """
        Parses a complete program:
        Program -> Declaration* EOF
        """
        decls = []
        while self.lexer.peek_token().type != 'EOF':
            decls.append(self.parse_declaration())
        return ProgramNode(decls)

    def parse_declaration(self):
        """
        Declaration -> VarDecl | FuncDef
        Both start with: Type ['*'] IDENT
        """
        t = self.lexer.peek_token()
        if t.type not in {'INT', 'CHAR', 'VOID'}:
            self._error(f"Expected type (int, char, void), got {t.value}")
        
        type_token = self.lexer.consume_token()
        type_name = type_token.value
        
        is_pointer = False
        if self.lexer.peek_token().type == 'MUL':
            self.lexer.consume_token()
            is_pointer = True
            
        ident_token = self._match('IDENT')
        name = ident_token.value
        
        next_t = self.lexer.peek_token()
        if next_t.type == 'LPAREN':
            # Function definition
            return self.parse_func_def(type_name, name, is_pointer, type_token.line)
        else:
            # Variable declaration
            return self.parse_var_decl_tail(type_name, name, is_pointer, type_token.line)

    def parse_var_decl_tail(self, type_name, name, is_pointer, line):
        """
        VarDeclTail -> '[' INT_CONST ']' ';' | '=' Expr ';' | ';'
        """
        array_size = None
        init_expr = None
        
        next_t = self.lexer.peek_token()
        if next_t.type == 'LBRACKET':
            self.lexer.consume_token()
            size_token = self._match('INT_CONST')
            array_size = size_token.value
            self._match('RBRACKET')
        elif next_t.type == 'ASSIGN':
            self.lexer.consume_token()
            init_expr = self.parse_expression()
            
        self._match('SEMI')
        return VarDeclNode(type_name, name, is_pointer, array_size, init_expr, line)

    def parse_func_def(self, return_type, name, is_pointer, line):
        """
        FuncDef -> '(' Params ')' '{' LocalDecls Stmt* '}'
        """
        self._match('LPAREN')
        params = self.parse_params()
        self._match('RPAREN')
        
        self._match('LBRACE')
        
        # Local variables must be declared at the beginning of the block
        local_decls = []
        while self.lexer.peek_token().type in {'INT', 'CHAR'}:
            local_decls.append(self.parse_local_var_decl())
            
        body = []
        while self.lexer.peek_token().type != 'RBRACE' and self.lexer.peek_token().type != 'EOF':
            body.append(self.parse_statement())
            
        self._match('RBRACE')
        return FuncDefNode(return_type, name, is_pointer, params, local_decls, body, line)

    def parse_local_var_decl(self):
        type_token = self.lexer.consume_token() # INT or CHAR
        type_name = type_token.value
        
        is_pointer = False
        if self.lexer.peek_token().type == 'MUL':
            self.lexer.consume_token()
            is_pointer = True
            
        ident_token = self._match('IDENT')
        name = ident_token.value
        
        return self.parse_var_decl_tail(type_name, name, is_pointer, type_token.line)

    def parse_params(self):
        """
        Params -> Param (',' Param)* | empty
        """
        params = []
        if self.lexer.peek_token().type == 'RPAREN':
            return params
            
        params.append(self.parse_param())
        while self.lexer.peek_token().type == 'COMMA':
            self.lexer.consume_token()
            params.append(self.parse_param())
        return params

    def parse_param(self):
        t = self.lexer.peek_token()
        if t.type not in {'INT', 'CHAR'}:
            self._error(f"Expected parameter type, got {t.value}")
        type_token = self.lexer.consume_token()
        type_name = type_token.value
        
        is_pointer = False
        if self.lexer.peek_token().type == 'MUL':
            self.lexer.consume_token()
            is_pointer = True
            
        ident_token = self._match('IDENT')
        name = ident_token.value
        return ParamDeclNode(type_name, name, is_pointer, type_token.line)

    def parse_statement(self):
        """
        Stmt -> BlockStmt | IfStmt | WhileStmt | ForStmt | DoWhileStmt | 
                BreakStmt | ContinueStmt | ReturnStmt | SwitchStmt | VarDecl | ExprStmt
        """
        t = self.lexer.peek_token()
        
        if t.type == 'LBRACE':
            return self.parse_block()
        elif t.type == 'IF':
            return self.parse_if()
        elif t.type == 'WHILE':
            return self.parse_while()
        elif t.type == 'FOR':
            return self.parse_for()
        elif t.type == 'DO':
            return self.parse_do_while()
        elif t.type in {'INT', 'CHAR'}:
            return self.parse_local_var_decl()
        elif t.type == 'BREAK':
            self.lexer.consume_token()
            self._match('SEMI')
            return BreakNode(t.line)
        elif t.type == 'CONTINUE':
            self.lexer.consume_token()
            self._match('SEMI')
            return ContinueNode(t.line)
        elif t.type == 'RETURN':
            self.lexer.consume_token()
            expr = None
            if self.lexer.peek_token().type != 'SEMI':
                expr = self.parse_expression()
            self._match('SEMI')
            return ReturnNode(expr, t.line)
        elif t.type == 'SWITCH':
            return self.parse_switch()
        else:
            # Expression statement
            expr = self.parse_expression()
            self._match('SEMI')
            return expr

    def parse_block(self):
        t = self._match('LBRACE')
        stmts = []
        while self.lexer.peek_token().type != 'RBRACE' and self.lexer.peek_token().type != 'EOF':
            stmts.append(self.parse_statement())
        self._match('RBRACE')
        return BlockNode(stmts, t.line)

    def parse_if(self):
        t = self._match('IF')
        self._match('LPAREN')
        cond = self.parse_expression()
        self._match('RPAREN')
        then_branch = self.parse_statement()
        
        else_branch = None
        if self.lexer.peek_token().type == 'ELSE':
            self.lexer.consume_token()
            else_branch = self.parse_statement()
            
        return IfNode(cond, then_branch, else_branch, t.line)

    def parse_while(self):
        t = self._match('WHILE')
        self._match('LPAREN')
        cond = self.parse_expression()
        self._match('RPAREN')
        body = self.parse_statement()
        return WhileNode(cond, body, t.line)

    def parse_for(self):
        t = self._match('FOR')
        self._match('LPAREN')
        
        init = None
        if self.lexer.peek_token().type != 'SEMI':
            init = self.parse_expression()
        self._match('SEMI')
        
        cond = None
        if self.lexer.peek_token().type != 'SEMI':
            cond = self.parse_expression()
        self._match('SEMI')
        
        step = None
        if self.lexer.peek_token().type != 'RPAREN':
            step = self.parse_expression()
        self._match('RPAREN')
        
        body = self.parse_statement()
        return ForNode(init, cond, step, body, t.line)

    def parse_do_while(self):
        t = self._match('DO')
        body = self.parse_statement()
        self._match('WHILE')
        self._match('LPAREN')
        cond = self.parse_expression()
        self._match('RPAREN')
        self._match('SEMI')
        return DoWhileNode(body, cond, t.line)

    def parse_switch(self):
        t = self._match('SWITCH')
        self._match('LPAREN')
        expr = self.parse_expression()
        self._match('RPAREN')
        
        self._match('LBRACE')
        cases = []
        default_case = None
        
        while self.lexer.peek_token().type in {'CASE', 'DEFAULT'}:
            case_t = self.lexer.consume_token()
            if case_t.type == 'CASE':
                # Small-C switch-case normally takes basic integer or char values
                val_token = self.lexer.peek_token()
                if val_token.type not in {'INT_CONST', 'HEX', 'CHAR_CONST'}:
                    self._error("Case value must be an integer, hex, or character constant")
                val_token = self.lexer.consume_token()
                val = val_token.value
                self._match('COLON')
                
                # Parse statements until next CASE, DEFAULT or RBRACE
                stmts = []
                while self.lexer.peek_token().type not in {'CASE', 'DEFAULT', 'RBRACE', 'EOF'}:
                    stmts.append(self.parse_statement())
                cases.append((val, stmts))
            else:
                self._match('COLON')
                stmts = []
                while self.lexer.peek_token().type not in {'CASE', 'DEFAULT', 'RBRACE', 'EOF'}:
                    stmts.append(self.parse_statement())
                default_case = stmts
                
        self._match('RBRACE')
        return SwitchNode(expr, cases, default_case, t.line)

    def parse_expression(self, precedence=0):
        left = self.parse_prefix()
        
        while True:
            token = self.lexer.peek_token()
            if token.type not in PRECEDENCE or PRECEDENCE[token.type] < precedence:
                break
            
            # Subscript and function call are handled as special infix operator checks
            token = self.lexer.consume_token()
            op_prec = PRECEDENCE[token.type]
            
            if token.type == 'LPAREN':
                # Function call, e.g., left(args)
                args = []
                if self.lexer.peek_token().type != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.lexer.peek_token().type == 'COMMA':
                        self.lexer.consume_token()
                        args.append(self.parse_expression())
                self._match('RPAREN')
                left = FuncCallNode(left, args, token.line)
            elif token.type == 'LBRACKET':
                # Array subscript, e.g., left[index]
                index_expr = self.parse_expression()
                self._match('RBRACKET')
                left = ArrayAccessNode(left, index_expr, token.line)
            else:
                # Normal binary operators or assignments
                is_assign = token.type in {'ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'MUL_ASSIGN', 'DIV_ASSIGN', 'MOD_ASSIGN'}
                next_prec = op_prec if is_assign else op_prec + 1
                right = self.parse_expression(next_prec)
                if is_assign:
                    left = AssignNode(left, token.type, right, token.line)
                else:
                    left = BinaryOpNode(token.type, left, right, token.line)
        return left

    def parse_prefix(self):
        t = self.lexer.consume_token()
        
        if t.type == 'INT_CONST':
            return LiteralNode(t.value, 'int', t.line)
        elif t.type == 'HEX':
            return LiteralNode(t.value, 'int', t.line)
        elif t.type == 'CHAR_CONST':
            return LiteralNode(t.value, 'char', t.line)
        elif t.type == 'STR_CONST':
            return LiteralNode(t.value, 'string', t.line)
        elif t.type == 'IDENT':
            return VariableNode(t.value, t.line)
        elif t.type == 'LPAREN':
            expr = self.parse_expression()
            self._match('RPAREN')
            return expr
        elif t.type == 'MINUS':
            # Unary minus
            expr = self.parse_expression(11) # High precedence
            return UnaryOpNode('MINUS', expr, t.line)
        elif t.type == 'EXCL':
            # Logical NOT
            expr = self.parse_expression(11)
            return UnaryOpNode('EXCL', expr, t.line)
        elif t.type == 'TILDE':
            # Bitwise NOT
            expr = self.parse_expression(11)
            return UnaryOpNode('TILDE', expr, t.line)
        elif t.type == 'AMP':
            # Address-of &
            expr = self.parse_expression(11)
            return AddressOfNode(expr, t.line)
        elif t.type == 'MUL':
            # Dereference *
            expr = self.parse_expression(11)
            return DereferenceNode(expr, t.line)
        elif t.type == 'INC':
            # Prefix ++
            expr = self.parse_expression(11)
            return UnaryOpNode('INC', expr, t.line)
        elif t.type == 'DEC':
            # Prefix --
            expr = self.parse_expression(11)
            return UnaryOpNode('DEC', expr, t.line)
        else:
            self._error(f"Unexpected prefix token {t.type} ({t.value})")
