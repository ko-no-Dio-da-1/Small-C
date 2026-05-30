from parser import (
    ProgramNode, VarDeclNode, FuncDefNode, ParamDeclNode, BlockNode,
    IfNode, WhileNode, ForNode, DoWhileNode, BreakNode, ContinueNode,
    ReturnNode, SwitchNode, AssignNode, BinaryOpNode, UnaryOpNode,
    AddressOfNode, DereferenceNode, ArrayAccessNode, FuncCallNode,
    VariableNode, LiteralNode
)
from symtable import Symbol
from memory import MemoryError
from sc_builtins import call_builtin, InterpreterExit

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class Interpreter:
    def __init__(self, memory, symtable):
        self.memory = memory
        self.symtable = symtable
        self.trace_enabled = False
        self.code_lines = []
        self.frame_counter = 0
        self.call_stack = [] # Stack of (frame_id, func_name)
        
    def set_code_lines(self, lines):
        self.code_lines = lines

    def _trace(self, line_num):
        if self.trace_enabled and line_num and 1 <= line_num <= len(self.code_lines):
            line_content = self.code_lines[line_num - 1].strip()
            print(f"[line {line_num}] {line_content}")

    def execute_program(self, program_ast):
        """
        Executes a top-level Program AST.
        """
        # First pass: Register all global declarations
        for decl in program_ast.declarations:
            if isinstance(decl, FuncDefNode):
                # Check for redefinition
                existing = self.symtable.lookup_global(decl.name)
                if existing and not existing.is_builtin:
                    # Overwrite/Redefine
                    existing.ast_node = decl
                    existing.params = [(p.type_name, p.is_pointer, p.name) for p in decl.params]
                else:
                    self.symtable.define(Symbol(
                        name=decl.name,
                        kind='func',
                        type_name=decl.return_type,
                        is_pointer=decl.is_pointer,
                        params=[(p.type_name, p.is_pointer, p.name) for p in decl.params],
                        ast_node=decl
                    ))
            elif isinstance(decl, VarDeclNode):
                self.declare_variable(decl, is_global=True)
                
        # Find main function
        main_sym = self.symtable.lookup_global('main')
        if not main_sym or main_sym.kind != 'func':
            raise RuntimeError("Linker error: main() function not defined")
            
        # Run main()
        try:
            return self.call_function('main', [], line=1)
        except InterpreterExit as e:
            return e.code

    def declare_variable(self, node, is_global=False):
        """
        Allocates memory for a variable declaration and registers it in Symbol Table.
        """
        # Evaluate initial value if exists
        init_val = 0
        if node.init_expr:
            init_val = self.evaluate(node.init_expr)
            
        size = node.array_size if node.array_size is not None else 1
        
        # Check redefinition in current scope
        if node.name in self.symtable.current_scope.symbols:
            raise RuntimeError(f"Redefinition of variable '{node.name}' at line {node.line}")
            
        if is_global:
            addr = self.memory.allocate_global(size, node.type_name, node.name, is_array=bool(node.array_size), is_pointer=node.is_pointer)
        else:
            addr = self.memory.allocate_stack(size, node.type_name, node.name, is_array=bool(node.array_size), is_pointer=node.is_pointer)
            
        # Register symbol
        sym = Symbol(
            name=node.name,
            kind='var',
            type_name=node.type_name,
            is_pointer=node.is_pointer,
            array_size=node.array_size,
            address=addr
        )
        self.symtable.define(sym)
        
        # Write initial value if not array
        if not node.array_size and node.init_expr:
            self.memory.write(addr, init_val, node.line)
            
        return addr

    def call_function(self, name, arg_values, line):
        symbol = self.symtable.lookup(name)
        if not symbol or symbol.kind != 'func':
            raise RuntimeError(f"Undefined function '{name}' called at line {line}")
            
        if symbol.is_builtin:
            return call_builtin(name, arg_values, self.memory, line)
            
        func_node = symbol.ast_node
        if len(func_node.params) != len(arg_values):
            raise RuntimeError(f"Function '{name}' expected {len(func_node.params)} arguments, got {len(arg_values)} at line {line}")
            
        # Push stack frame
        self.frame_counter += 1
        fid = self.frame_counter
        self.call_stack.append((fid, name))
        
        prev_fid = self.memory.current_frame_id
        prev_sp = self.memory.get_stack_ptr()
        self.memory.set_frame_id(fid)
        
        # Scope transitions
        self.symtable.enter_scope()
        
        try:
            # 1. Allocate parameter variables
            for idx, param in enumerate(func_node.params):
                # Correctly pass False for is_array (parameters are scalar/pointers, not arrays)
                # Correctly pass param.is_pointer for is_pointer
                addr = self.memory.allocate_stack(1, param.type_name, param.name, False, param.is_pointer)
                self.symtable.define(Symbol(
                    name=param.name,
                    kind='var',
                    type_name=param.type_name,
                    is_pointer=param.is_pointer,
                    address=addr
                ))
                self.memory.write(addr, arg_values[idx], line)
                
            # 2. Allocate local variables
            for decl in func_node.decls:
                self.declare_variable(decl, is_global=False)
                
            # 3. Execute function statements
            for stmt in func_node.body:
                self.execute(stmt)
                
            ret_val = 0 # Default return if none specified
        except ReturnException as r:
            ret_val = r.value
        finally:
            # Cleanup
            self.symtable.exit_scope()
            self.memory.deallocate_frame(fid, prev_sp)
            self.call_stack.pop()
            self.memory.set_frame_id(prev_fid)
            
        return ret_val

    def execute(self, node):
        if not node:
            return
            
        # Trace statement before execution
        if isinstance(node, (AssignNode, IfNode, WhileNode, ForNode, DoWhileNode, ReturnNode, BreakNode, ContinueNode, FuncCallNode, SwitchNode)):
            self._trace(node.line)
            
        if isinstance(node, BlockNode):
            self.symtable.enter_scope()
            saved_sp = self.memory.get_stack_ptr()
            try:
                for stmt in node.statements:
                    self.execute(stmt)
            finally:
                self.symtable.exit_scope()
                # Only deallocate if we are on stack (frame_id is not None)
                if self.memory.current_frame_id is not None:
                    self.memory.deallocate_to_stack_ptr(saved_sp)
                
        elif isinstance(node, VarDeclNode):
            # Local var decls are handled by call_function. If we meet one here (e.g. in interactive mode), run it.
            self.declare_variable(node, is_global=(self.memory.current_frame_id is None))
            
        elif isinstance(node, IfNode):
            cond_val = self.evaluate(node.cond)
            if cond_val != 0:
                self.execute(node.then_branch)
            elif node.else_branch:
                self.execute(node.else_branch)
                
        elif isinstance(node, WhileNode):
            while True:
                cond_val = self.evaluate(node.cond)
                if cond_val == 0:
                    break
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
                    
        elif isinstance(node, ForNode):
            if node.init:
                self.evaluate(node.init) # evaluate L-value/assignment init
            while True:
                if node.cond:
                    cond_val = self.evaluate(node.cond)
                    if cond_val == 0:
                        break
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass
                if node.step:
                    self.evaluate(node.step)
                    
        elif isinstance(node, DoWhileNode):
            while True:
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass
                cond_val = self.evaluate(node.cond)
                if cond_val == 0:
                    break
                    
        elif isinstance(node, BreakNode):
            raise BreakException()
            
        elif isinstance(node, ContinueNode):
            raise ContinueException()
            
        elif isinstance(node, ReturnNode):
            val = 0
            if node.expr:
                val = self.evaluate(node.expr)
            raise ReturnException(val)
            
        elif isinstance(node, SwitchNode):
            val = self.evaluate(node.expr)
            matched = False
            try:
                # Find matching case
                matched_idx = -1
                for idx, (case_val, _) in enumerate(node.cases):
                    if val == case_val:
                        matched_idx = idx
                        break
                
                if matched_idx != -1:
                    matched = True
                    # Execute matching case and subsequent fall-throughs
                    for idx in range(matched_idx, len(node.cases)):
                        _, stmts = node.cases[idx]
                        for stmt in stmts:
                            self.execute(stmt)
                    # Execute default too if no break
                    if node.default_case:
                        for stmt in node.default_case:
                            self.execute(stmt)
                elif node.default_case:
                    # Execute default
                    for stmt in node.default_case:
                        self.execute(stmt)
            except BreakException:
                pass # Switch break exits the switch
                
        else:
            # Fallback to evaluate expression statements (like function calls or standalone expressions)
            self.evaluate(node)

    def evaluate_lvalue(self, node):
        """
        Evaluates the node as an L-value (assignable target) and returns its virtual memory address.
        """
        if isinstance(node, VariableNode):
            sym = self.symtable.lookup(node.name)
            if not sym or sym.kind != 'var':
                raise RuntimeError(f"Undefined variable '{node.name}' at line {node.line}")
            if sym.array_size is not None:
                raise RuntimeError(f"Cannot assign directly to array name '{node.name}' at line {node.line}")
            return sym.address
            
        elif isinstance(node, DereferenceNode):
            return self.evaluate(node.expr)
            
        elif isinstance(node, ArrayAccessNode):
            base_addr = self.evaluate(node.array_expr)
            idx = self.evaluate(node.index_expr)
            return base_addr + idx
            
        else:
            raise RuntimeError(f"Expression on line {node.line} is not a modifiable L-value")

    def evaluate(self, node):
        if not node:
            return 0
            
        if isinstance(node, LiteralNode):
            if node.type == 'string':
                # Allocate literal in heap and return its address
                return self.memory.allocate_string(node.value)
            return node.value
            
        elif isinstance(node, VariableNode):
            sym = self.symtable.lookup(node.name)
            if not sym:
                raise RuntimeError(f"Undefined variable '{node.name}' at line {node.line}")
            if sym.kind == 'func':
                # Function pointer equivalent or reference (not fully supported by Small-C, return mock addr or symbol)
                return 0
            if sym.array_size is not None:
                # Array decays to pointer (address of first element)
                return sym.address
            return self.memory.read(sym.address, node.line)
            
        elif isinstance(node, DereferenceNode):
            addr = self.evaluate(node.expr)
            return self.memory.read(addr, node.line)
            
        elif isinstance(node, AddressOfNode):
            return self.evaluate_lvalue(node.expr)
            
        elif isinstance(node, ArrayAccessNode):
            base_addr = self.evaluate(node.array_expr)
            idx = self.evaluate(node.index_expr)
            return self.memory.read(base_addr + idx, node.line)
            
        elif isinstance(node, FuncCallNode):
            # Evaluate arguments
            arg_vals = [self.evaluate(arg) for arg in node.args]
            # Resolve function name
            if isinstance(node.name_expr, VariableNode):
                func_name = node.name_expr.name
            else:
                raise RuntimeError(f"Dynamic function pointers not supported at line {node.line}")
            return self.call_function(func_name, arg_vals, node.line)
            
        elif isinstance(node, UnaryOpNode):
            if node.op == 'MINUS':
                return -self.evaluate(node.expr)
            elif node.op == 'EXCL':
                return 1 if self.evaluate(node.expr) == 0 else 0
            elif node.op == 'TILDE':
                return ~self.evaluate(node.expr)
            elif node.op in {'INC', 'DEC'}:
                addr = self.evaluate_lvalue(node.expr)
                curr = self.memory.read(addr, node.line)
                new_val = curr + 1 if node.op == 'INC' else curr - 1
                self.memory.write(addr, new_val, node.line)
                return new_val
                
        elif isinstance(node, AssignNode):
            addr = self.evaluate_lvalue(node.left)
            rval = self.evaluate(node.right)
            
            if node.op == 'ASSIGN':
                val = rval
            else:
                curr = self.memory.read(addr, node.line)
                if node.op == 'ADD_ASSIGN':
                    val = curr + rval
                elif node.op == 'SUB_ASSIGN':
                    val = curr - rval
                elif node.op == 'MUL_ASSIGN':
                    val = curr * rval
                elif node.op == 'DIV_ASSIGN':
                    if rval == 0:
                        raise MemoryError("division by zero", node.line)
                    val = int(curr / rval)
                elif node.op == 'MOD_ASSIGN':
                    if rval == 0:
                        raise MemoryError("division by zero", node.line)
                    val = curr - int(curr / rval) * rval
            
            self.memory.write(addr, val, node.line)
            return val
            
        elif isinstance(node, BinaryOpNode):
            # Handle logical short-circuit evaluation first
            if node.op == 'AND':
                lval = self.evaluate(node.left)
                if lval == 0:
                    return 0
                rval = self.evaluate(node.right)
                return 1 if rval != 0 else 0
            elif node.op == 'OR':
                lval = self.evaluate(node.left)
                if lval != 0:
                    return 1
                rval = self.evaluate(node.right)
                return 1 if rval != 0 else 0
                
            lval = self.evaluate(node.left)
            rval = self.evaluate(node.right)
            
            if node.op == 'PLUS':
                return lval + rval
            elif node.op == 'MINUS':
                return lval - rval
            elif node.op == 'MUL':
                return lval * rval
            elif node.op == 'DIV':
                if rval == 0:
                    raise MemoryError("division by zero", node.line)
                return int(lval / rval)
            elif node.op == 'MOD':
                if rval == 0:
                    raise MemoryError("division by zero", node.line)
                return lval - int(lval / rval) * rval
            elif node.op == 'LT':
                return 1 if lval < rval else 0
            elif node.op == 'LE':
                return 1 if lval <= rval else 0
            elif node.op == 'GT':
                return 1 if lval > rval else 0
            elif node.op == 'GE':
                return 1 if lval >= rval else 0
            elif node.op == 'EQ':
                return 1 if lval == rval else 0
            elif node.op == 'NE':
                return 1 if lval != rval else 0
            elif node.op == 'AMP':
                return lval & rval
            elif node.op == 'BAR':
                return lval | rval
            elif node.op == 'CARET':
                return lval ^ rval
            elif node.op == 'SHL':
                return lval << rval
            elif node.op == 'SHR':
                return lval >> rval
                
        return 0
