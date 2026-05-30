import sys
import re
import math
from memory import MemoryError

# POSIX LCG State
_lcg_state = 1

class InterpreterExit(Exception):
    def __init__(self, code):
        super().__init__(f"Exit with code {code}")
        self.code = code

def call_builtin(name, args, memory, line):
    global _lcg_state
    
    if name == 'putchar':
        ch = args[0]
        sys.stdout.write(chr(ch))
        sys.stdout.flush()
        return ch
        
    elif name == 'getchar':
        ch = sys.stdin.read(1)
        return ord(ch) if ch else -1
        
    elif name == 'printf':
        if not args:
            return None
        fmt_addr = args[0]
        fmt_str = memory.read_string(fmt_addr, line)
        
        arg_idx = 1
        out = []
        i = 0
        while i < len(fmt_str):
            if fmt_str[i] == '%' and i + 1 < len(fmt_str):
                spec = fmt_str[i+1]
                if spec == '%':
                    out.append('%')
                elif spec == 'd':
                    if arg_idx < len(args):
                        out.append(str(args[arg_idx]))
                        arg_idx += 1
                    else:
                        out.append("<missing arg>")
                elif spec == 'c':
                    if arg_idx < len(args):
                        out.append(chr(args[arg_idx]))
                        arg_idx += 1
                    else:
                        out.append("<missing arg>")
                elif spec == 's':
                    if arg_idx < len(args):
                        str_addr = args[arg_idx]
                        str_val = memory.read_string(str_addr, line)
                        out.append(str_val)
                        arg_idx += 1
                    else:
                        out.append("<missing arg>")
                elif spec == 'x':
                    if arg_idx < len(args):
                        val = args[arg_idx]
                        if val < 0:
                            val = (val + 2**32) % 2**32
                        out.append(f"{val:x}")
                        arg_idx += 1
                    else:
                        out.append("<missing arg>")
                else:
                    out.append('%' + spec)
                i += 2
            else:
                out.append(fmt_str[i])
                i += 1
        sys.stdout.write("".join(out))
        sys.stdout.flush()
        return None
        
    elif name == 'puts':
        str_addr = args[0]
        s_val = memory.read_string(str_addr, line)
        sys.stdout.write(s_val + '\n')
        sys.stdout.flush()
        return None
        
    elif name == 'scanf':
        if not args:
            return 0
        fmt_addr = args[0]
        fmt_str = memory.read_string(fmt_addr, line)
        specs = re.findall(r'%[dcsx]', fmt_str)
        if not specs:
            return 0
            
        line_in = sys.stdin.readline()
        tokens = line_in.split()
        
        success_count = 0
        for idx, spec in enumerate(specs):
            if idx >= len(tokens) or (idx + 1) >= len(args):
                break
            token = tokens[idx]
            dest_addr = args[idx + 1]
            
            if spec == '%d':
                try:
                    val = int(token)
                    memory.write(dest_addr, val, line)
                    success_count += 1
                except ValueError:
                    break
            elif spec == '%c':
                if len(token) > 0:
                    val = ord(token[0])
                    memory.write(dest_addr, val, line)
                    success_count += 1
            elif spec == '%s':
                memory.write_string(dest_addr, token, line)
                success_count += 1
            elif spec == '%x':
                try:
                    val = int(token, 16)
                    memory.write(dest_addr, val, line)
                    success_count += 1
                except ValueError:
                    break
                    
        return success_count
        
    elif name == 'strlen':
        return len(memory.read_string(args[0], line))
        
    elif name == 'strcpy':
        dest = args[0]
        src = args[1]
        s_val = memory.read_string(src, line)
        memory.write_string(dest, s_val, line)
        return None
        
    elif name == 'strcmp':
        val1 = memory.read_string(args[0], line)
        val2 = memory.read_string(args[1], line)
        if val1 < val2:
            return -1
        elif val1 > val2:
            return 1
        else:
            return 0
            
    elif name == 'strcat':
        dest = args[0]
        src = args[1]
        dest_val = memory.read_string(dest, line)
        src_val = memory.read_string(src, line)
        memory.write_string(dest, dest_val + src_val, line)
        return None
        
    elif name == 'abs':
        return abs(args[0])
        
    elif name == 'max':
        return max(args[0], args[1])
        
    elif name == 'min':
        return min(args[0], args[1])
        
    elif name == 'pow':
        base = args[0]
        exp = args[1]
        if exp < 0:
            return 0
        return int(base ** exp)
        
    elif name == 'sqrt':
        x = args[0]
        if x < 0:
            raise MemoryError("sqrt argument must be non-negative", line)
        return math.isqrt(x)
        
    elif name == 'mod':
        a = args[0]
        b = args[1]
        if b == 0:
            raise MemoryError("division by zero", line)
        return a % b
        
    elif name == 'rand':
        _lcg_state = (1103515245 * _lcg_state + 12345) % 2**31
        return (_lcg_state // 65536) % 32768
        
    elif name == 'srand':
        _lcg_state = args[0]
        return None
        
    elif name == 'memset':
        addr = args[0]
        val = args[1]
        size = args[2]
        for i in range(size):
            memory.write(addr + i, val, line)
        return None
        
    elif name == 'sizeof_int':
        return 4
        
    elif name == 'sizeof_char':
        return 1
        
    elif name == 'atoi':
        s_val = memory.read_string(args[0], line)
        match = re.match(r'^\s*([-+]?\d+)', s_val)
        if match:
            return int(match.group(1))
        return 0
        
    elif name == 'itoa':
        val = args[0]
        dest = args[1]
        memory.write_string(dest, str(val), line)
        return None
        
    elif name == 'exit':
        raise InterpreterExit(args[0])
        
    else:
        raise RuntimeError(f"Unknown built-in function '{name}'")
