class Symbol:
    def __init__(self, name, kind, type_name, is_pointer=False, array_size=None, address=None, params=None, ast_node=None, is_builtin=False):
        self.name = name
        self.kind = kind            # 'var' or 'func'
        self.type_name = type_name  # 'int', 'char', 'void'
        self.is_pointer = is_pointer
        self.array_size = array_size
        self.address = address      # Memory address if variable
        self.params = params        # List of Param info for function
        self.ast_node = ast_node    # AST node for user-defined function
        self.is_builtin = is_builtin

    def __repr__(self):
        return f"Symbol({self.name}, kind={self.kind}, type={self.type_name}, is_ptr={self.is_pointer}, addr={self.address})"

class Scope:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, symbol):
        self.symbols[symbol.name] = symbol

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

class SymbolTable:
    def __init__(self):
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self._register_builtins()

    def enter_scope(self):
        self.current_scope = Scope(self.current_scope)

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define(self, symbol):
        self.current_scope.define(symbol)

    def lookup(self, name):
        return self.current_scope.lookup(name)

    def lookup_global(self, name):
        return self.global_scope.symbols.get(name)

    def _register_builtins(self):
        # I/O functions
        self.global_scope.define(Symbol('putchar', 'func', 'int', params=[('int', False, 'ch')], is_builtin=True))
        self.global_scope.define(Symbol('getchar', 'func', 'int', params=[], is_builtin=True))
        self.global_scope.define(Symbol('printf', 'func', 'void', params=[('char', True, 'fmt')], is_builtin=True)) # varargs
        self.global_scope.define(Symbol('puts', 'func', 'void', params=[('char', True, 's')], is_builtin=True))
        self.global_scope.define(Symbol('scanf', 'func', 'int', params=[('char', True, 'fmt')], is_builtin=True)) # varargs
        
        # String functions
        self.global_scope.define(Symbol('strlen', 'func', 'int', params=[('char', True, 's')], is_builtin=True))
        self.global_scope.define(Symbol('strcpy', 'func', 'void', params=[('char', True, 'dest'), ('char', True, 'src')], is_builtin=True))
        self.global_scope.define(Symbol('strcmp', 'func', 'int', params=[('char', True, 's1'), ('char', True, 's2')], is_builtin=True))
        self.global_scope.define(Symbol('strcat', 'func', 'void', params=[('char', True, 'dest'), ('char', True, 'src')], is_builtin=True))
        
        # Math functions
        self.global_scope.define(Symbol('abs', 'func', 'int', params=[('int', False, 'x')], is_builtin=True))
        self.global_scope.define(Symbol('max', 'func', 'int', params=[('int', False, 'a'), ('int', False, 'b')], is_builtin=True))
        self.global_scope.define(Symbol('min', 'func', 'int', params=[('int', False, 'a'), ('int', False, 'b')], is_builtin=True))
        self.global_scope.define(Symbol('pow', 'func', 'int', params=[('int', False, 'base'), ('int', False, 'exp')], is_builtin=True))
        self.global_scope.define(Symbol('sqrt', 'func', 'int', params=[('int', False, 'x')], is_builtin=True))
        self.global_scope.define(Symbol('mod', 'func', 'int', params=[('int', False, 'a'), ('int', False, 'b')], is_builtin=True))
        self.global_scope.define(Symbol('rand', 'func', 'int', params=[], is_builtin=True))
        self.global_scope.define(Symbol('srand', 'func', 'void', params=[('int', False, 'seed')], is_builtin=True))
        
        # Utility & memory
        self.global_scope.define(Symbol('memset', 'func', 'void', params=[('char', True, 'ptr'), ('int', False, 'val'), ('int', False, 'size')], is_builtin=True))
        self.global_scope.define(Symbol('sizeof_int', 'func', 'int', params=[], is_builtin=True))
        self.global_scope.define(Symbol('sizeof_char', 'func', 'int', params=[], is_builtin=True))
        self.global_scope.define(Symbol('atoi', 'func', 'int', params=[('char', True, 's')], is_builtin=True))
        self.global_scope.define(Symbol('itoa', 'func', 'void', params=[('int', False, 'val'), ('char', True, 'str')], is_builtin=True))
        self.global_scope.define(Symbol('exit', 'func', 'void', params=[('int', False, 'code')], is_builtin=True))
