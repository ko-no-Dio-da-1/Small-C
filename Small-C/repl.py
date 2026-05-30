import os
import sys
import re
from lexer import Lexer, LexicalError
from parser import Parser, SyntaxError, VarDeclNode, FuncDefNode
from interpreter import Interpreter, MemoryError
from symtable import SymbolTable, Symbol
from memory import Memory

class REPL:
    def __init__(self):
        self.buffer = [] # Code buffer (list of strings)
        self.modified = False
        self.current_file = None
        
        # Shared active environment for interactive execution
        self.memory = Memory()
        self.symtable = SymbolTable()
        self.interpreter = Interpreter(self.memory, self.symtable)
        
    def reset_env(self):
        """
        Resets the environment for a clean RUN.
        Preserves trace settings.
        """
        trace = self.interpreter.trace_enabled
        self.memory = Memory()
        self.symtable = SymbolTable()
        self.interpreter = Interpreter(self.memory, self.symtable)
        self.interpreter.trace_enabled = trace

    def print_help(self, cmd_arg=None):
        if cmd_arg:
            cmd = cmd_arg.upper()
            help_details = {
                'LOAD': "LOAD <filename> : Load a Small-C program file into the buffer.",
                'SAVE': "SAVE <filename> : Save the current buffer to a file.",
                'LIST': "LIST [n | n1-n2] : List all lines, a single line, or a range of lines in the buffer.",
                'EDIT': "EDIT <n> : Edit the content of line n in the buffer.",
                'DELETE': "DELETE <n | n1-n2> : Delete line n or range n1-n2 in the buffer.",
                'INSERT': "INSERT <n> : Insert lines at line n. Enter '.' on a new line to finish.",
                'APPEND': "APPEND : Append lines to the end of the buffer. Enter '.' on a new line to finish.",
                'NEW': "NEW : Clear the buffer and reset the interactive environment.",
                'RUN': "RUN : Compile the current buffer and execute its main() function.",
                'CHECK': "CHECK : Verify syntax and semantics of the buffer without executing.",
                'TRACE': "TRACE <ON|OFF> : Turn execution tracing on or off.",
                'VARS': "VARS : Display all current variables and their values.",
                'FUNCS': "FUNCS : List all user-defined and built-in functions.",
                'HELP': "HELP [cmd] : Show command help summary or detailed info.",
                'ABOUT': "ABOUT : Show interpreter name, version, author, and course info.",
                'CLEAR': "CLEAR : Clear the terminal screen.",
                'QUIT': "QUIT / EXIT : Quit the Small-C interpreter.",
                'EXIT': "QUIT / EXIT : Quit the Small-C interpreter."
            }
            if cmd in help_details:
                print(help_details[cmd])
            else:
                print(f"Unknown command '{cmd_arg}'. Type HELP for a list of commands.")
            return

        print("=== Small-C Interactive REPL Commands ===")
        print("LOAD <file>      - Load code from file")
        print("SAVE <file>      - Save code to file")
        print("LIST [range]     - List buffer (e.g., LIST, LIST 5, LIST 1-10)")
        print("EDIT <n>         - Edit line n")
        print("DELETE <range>   - Delete line(s) (e.g., DELETE 5, DELETE 1-5)")
        print("INSERT <n>       - Insert lines before line n")
        print("APPEND           - Append lines to the end")
        print("NEW              - Clear buffer & environment")
        print("RUN              - Compile and run main()")
        print("CHECK            - Parse and check for errors")
        print("TRACE <ON|OFF>   - Toggle execution tracing")
        print("VARS             - Show variables & memory")
        print("FUNCS            - Show defined functions")
        print("HELP [cmd]       - Show command help summary")
        print("ABOUT            - Show interpreter information")
        print("CLEAR            - Clear screen")
        print("QUIT/EXIT        - Quit interpreter")

    def print_about(self):
        print("==============================================")
        print(" Small-C Interactive Interpreter v1.0")
        print(" Author: 柯誌榕")  
        print(" Course: System Software Final Project")
        print(" Semester: Spring 2026")
        print(" Developed in Python 3")
        print("==============================================")

    def check_modified_and_confirm(self):
        if self.modified:
            ans = input("You have unsaved changes. Discard changes? (y/n): ").strip().lower()
            return ans == 'y'
        return True

    def run(self):
        self.print_about()
        print("Type 'HELP' for a list of commands.")
        
        while True:
            try:
                line_in = input("sc> ")
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye.")
                break
                
            stripped = line_in.strip()
            if not stripped:
                continue
                
            # Parse command
            parts = stripped.split(maxsplit=1)
            cmd = parts[0].upper()
            cmd_arg = parts[1] if len(parts) > 1 else None
            
            # REPL Command dispatch
            if cmd == 'QUIT' or cmd == 'EXIT':
                if self.check_modified_and_confirm():
                    print("Goodbye.")
                    break
                    
            elif cmd == 'HELP':
                self.print_help(cmd_arg)
                
            elif cmd == 'ABOUT':
                self.print_about()
                
            elif cmd == 'CLEAR':
                # Clear terminal
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\033[H\033[J", end="") # escape sequence fallback
                
            elif cmd == 'NEW':
                if self.check_modified_and_confirm():
                    self.buffer = []
                    self.modified = False
                    self.current_file = None
                    self.reset_env()
                    print("All cleared.")
                    
            elif cmd == 'LOAD':
                if not cmd_arg:
                    print("Usage: LOAD <filename>")
                    continue
                if self.check_modified_and_confirm():
                    filename = cmd_arg.strip('"\'')
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            self.buffer = [line.rstrip('\r\n') for line in f]
                        self.current_file = filename
                        self.modified = False
                        print(f"Loaded {len(self.buffer)} lines from '{filename}'.")
                    except FileNotFoundError:
                        print(f"Error: File '{filename}' not found.")
                    except Exception as e:
                        print(f"Error loading file: {e}")
                        
            elif cmd == 'SAVE':
                filename = cmd_arg.strip('"\'') if cmd_arg else self.current_file
                if not filename:
                    print("Error: No filename specified. Usage: SAVE <filename>")
                    continue
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        for line in self.buffer:
                            f.write(line + '\n')
                    self.current_file = filename
                    self.modified = False
                    print(f"Saved {len(self.buffer)} lines to '{filename}'.")
                except Exception as e:
                    print(f"Error saving file: {e}")
                    
            elif cmd == 'LIST':
                self.handle_list(cmd_arg)
                
            elif cmd == 'EDIT':
                if not cmd_arg:
                    print("Usage: EDIT <line_number>")
                    continue
                try:
                    n = int(cmd_arg)
                    if 1 <= n <= len(self.buffer):
                        print(f"Current line {n}: {self.buffer[n-1]}")
                        new_line = input(f"New line {n}: ")
                        if new_line:  # Only change if user typed something
                            self.buffer[n-1] = new_line
                            self.modified = True
                            print("Line updated.")
                        else:
                            print("Line unchanged.")
                    else:
                        print(f"Error: Line number {n} out of range (1 to {len(self.buffer)}).")
                except ValueError:
                    print("Error: Invalid line number.")
                    
            elif cmd == 'DELETE':
                if not cmd_arg:
                    print("Usage: DELETE <line_number> or DELETE <n1>-<n2>")
                    continue
                self.handle_delete(cmd_arg)
                
            elif cmd == 'INSERT':
                if not cmd_arg:
                    print("Usage: INSERT <line_number>")
                    continue
                try:
                    n = int(cmd_arg)
                    if 1 <= n <= len(self.buffer) + 1:
                        self.handle_insert(n)
                    else:
                        print(f"Error: Cannot insert at line {n}. Buffer size is {len(self.buffer)}.")
                except ValueError:
                    print("Error: Invalid line number.")
                    
            elif cmd == 'APPEND':
                self.handle_insert(len(self.buffer) + 1)
                
            elif cmd == 'TRACE':
                if cmd_arg and cmd_arg.upper() == 'ON':
                    self.interpreter.trace_enabled = True
                    print("Trace mode enabled.")
                elif cmd_arg and cmd_arg.upper() == 'OFF':
                    self.interpreter.trace_enabled = False
                    print("Trace mode disabled.")
                else:
                    print("Usage: TRACE <ON|OFF>")
                    
            elif cmd == 'VARS':
                vars_list = self.memory.dump_vars()
                if vars_list:
                    for v in vars_list:
                        print(v)
                else:
                    print("No variables declared.")
                    
            elif cmd == 'FUNCS':
                self.handle_funcs()
                
            elif cmd == 'CHECK':
                self.handle_compile(execute=False)
                
            elif cmd == 'RUN':
                self.handle_compile(execute=True)
                
            else:
                # Direct mode: immediate statement execution
                self.handle_direct_execution(line_in)

    def handle_list(self, arg):
        if not self.buffer:
            print("Buffer is empty.")
            return
            
        if not arg:
            start, end = 1, len(self.buffer)
        elif '-' in arg:
            match = re.match(r'^(\d+)-(\d+)$', arg.strip())
            if match:
                start, end = int(match.group(1)), int(match.group(2))
            else:
                print("Error: Invalid range format. Use n1-n2.")
                return
        else:
            try:
                start = end = int(arg)
            except ValueError:
                print("Error: Invalid line number.")
                return
                
        start = max(1, start)
        end = min(len(self.buffer), end)
        
        if start > end:
            print("Error: Invalid range.")
            return
            
        for i in range(start, end + 1):
            print(f"{i:4}> {self.buffer[i-1]}")

    def handle_delete(self, arg):
        if not self.buffer:
            print("Buffer is empty.")
            return
            
        if '-' in arg:
            match = re.match(r'^(\d+)-(\d+)$', arg.strip())
            if match:
                start, end = int(match.group(1)), int(match.group(2))
            else:
                print("Error: Invalid range format. Use n1-n2.")
                return
        else:
            try:
                start = end = int(arg)
            except ValueError:
                print("Error: Invalid line number.")
                return
                
        if start < 1 or end > len(self.buffer) or start > end:
            print("Error: Range out of bounds.")
            return
            
        # Delete lines (0-indexed)
        del self.buffer[start-1:end]
        self.modified = True
        print(f"Deleted lines {start} to {end}.")

    def handle_insert(self, start_line):
        print(f"Entering insert mode at line {start_line}. Type '.' on a separate line to exit.")
        lines_to_insert = []
        curr = start_line
        while True:
            try:
                line = input(f"{curr:4}> ")
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if line.strip() == '.':
                break
            lines_to_insert.append(line)
            curr += 1
            
        if lines_to_insert:
            self.buffer[start_line-1:start_line-1] = lines_to_insert
            self.modified = True
            print(f"Inserted {len(lines_to_insert)} lines.")

    def handle_funcs(self):
        user_funcs = []
        builtin_funcs = []
        
        # Look in global scope
        for sym_name, sym in sorted(self.symtable.global_scope.symbols.items()):
            if sym.kind == 'func':
                ptr_str = "*" if sym.is_pointer else ""
                param_strs = []
                for p_type, p_ptr, p_name in sym.params:
                    p_ptr_str = "*" if p_ptr else ""
                    param_strs.append(f"{p_type} {p_ptr_str}{p_name}")
                param_list = ", ".join(param_strs)
                
                sig = f"{sym.type_name} {ptr_str}{sym_name}({param_list})"
                
                if sym.is_builtin:
                    builtin_funcs.append(sig + " [built-in]")
                else:
                    line_info = f" (line {sym.ast_node.line})" if sym.ast_node else ""
                    user_funcs.append(sig + line_info)
                    
        print("--- User Defined Functions ---")
        if user_funcs:
            for f in user_funcs:
                print(f)
        else:
            print("None")
            
        print("\n--- Built-in Functions ---")
        for f in builtin_funcs:
            print(f)

    def handle_compile(self, execute=True):
        if not self.buffer:
            print("Buffer is empty.")
            return False
            
        code = "\n".join(self.buffer)
        
        try:
            lexer = Lexer(code)
            parser = Parser(lexer)
            program_ast = parser.parse()
            
            if not execute:
                print("No errors found.")
                return True
                
            # Setup environment for fresh run
            self.reset_env()
            self.interpreter.set_code_lines(self.buffer)
            
            # Execute
            ret = self.interpreter.execute_program(program_ast)
            print(f"Program exited with return value {ret}.")
            return True
            
        except LexicalError as e:
            print(f"Lexical Error at line {e.line}, col {e.col}: {e.message}")
        except SyntaxError as e:
            print(f"Syntax Error at line {e.line}, col {e.col}: {e.message}")
        except MemoryError as e:
            print(f"Runtime Memory Error at line {e.line or 'unknown'}: {e.message}")
        except Exception as e:
            # Internal or other runtime error
            import traceback
            # traceback.print_exc() # uncomment for debugging interpreter
            print(f"Runtime Error: {e}")
        return False

    def handle_direct_execution(self, initial_line):
        lines = [initial_line]
        
        # Check braces balance
        def get_brace_balance(text):
            # Strip comments first
            clean_text = re.sub(r'//[^\n]*', '', text)
            clean_text = re.sub(r'/\*.*?\*/', '', clean_text, flags=re.DOTALL)
            
            # Count braces ignoring chars/strings
            # Simple brace count
            open_braces = clean_text.count('{')
            close_braces = clean_text.count('}')
            return open_braces - close_braces

        balance = get_brace_balance(initial_line)
        while balance > 0:
            try:
                line = input("  > ")
            except (KeyboardInterrupt, EOFError):
                print()
                return
            lines.append(line)
            balance += get_brace_balance(line)
            
        code = "\n".join(lines)
        
        try:
            # Tokenize direct input
            lexer = Lexer(code)
            
            if not lexer.tokens or lexer.tokens[0].type == 'EOF':
                return
                
            first_t = lexer.tokens[0]
            
            parser = Parser(lexer)
            self.interpreter.set_code_lines(lines)
            
            # Determine if it's a declaration or a statement
            # Declarations in Small-C start with type specifiers: INT, CHAR, VOID
            if first_t.type in {'INT', 'CHAR', 'VOID'}:
                decl_ast = parser.parse_declaration()
                # If a function is defined in direct mode, register it
                if isinstance(decl_ast, FuncDefNode):
                    self.symtable.define(Symbol(
                        name=decl_ast.name,
                        kind='func',
                        type_name=decl_ast.return_type,
                        is_pointer=decl_ast.is_pointer,
                        params=[(p.type_name, p.is_pointer, p.name) for p in decl_ast.params],
                        ast_node=decl_ast
                    ))
                    print(f"Function '{decl_ast.name}' defined.")
                else:
                    # Variable declaration
                    # Global allocation since we are executing in active global environment
                    self.interpreter.declare_variable(decl_ast, is_global=True)
            else:
                # Execute statement
                stmt_ast = parser.parse_statement()
                self.interpreter.execute(stmt_ast)
                
        except LexicalError as e:
            print(f"Lexical Error: {e.message}")
        except SyntaxError as e:
            print(f"Syntax Error: {e.message}")
        except MemoryError as e:
            print(f"Runtime Memory Error: {e.message}")
        except Exception as e:
            print(f"Runtime Error: {e}")
