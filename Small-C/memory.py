class MemoryError(Exception):
    def __init__(self, message, line=None):
        super().__init__(message)
        self.message = message
        self.line = line

class Memory:
    def __init__(self):
        self.mem = {}  # address (int) -> value (int)
        
        # Memory segment pointers
        self.global_ptr = 1000
        self.stack_ptr = 100000
        self.heap_ptr = 500000
        
        # Allocations record: address -> (size, type_name, name, is_array, is_pointer, frame_id)
        # frame_id is None for globals/heap, and integer for stack frames
        self.allocations = {}
        
        # Keep track of active frame ID to tag allocations
        self.current_frame_id = None

    def set_frame_id(self, frame_id):
        self.current_frame_id = frame_id

    def allocate_global(self, size, type_name, name, is_array=False, is_pointer=False):
        addr = self.global_ptr
        self.global_ptr += size
        self.allocations[addr] = (size, type_name, name, is_array, is_pointer, None)
        # Initialize memory cells to 0
        for i in range(size):
            self.mem[addr + i] = 0
        return addr

    def allocate_stack(self, size, type_name, name, is_array=False, is_pointer=False):
        if self.current_frame_id is None:
            raise MemoryError("Cannot allocate on stack: no active stack frame")
        addr = self.stack_ptr
        self.stack_ptr += size
        self.allocations[addr] = (size, type_name, name, is_array, is_pointer, self.current_frame_id)
        # Initialize memory cells to 0
        for i in range(size):
            self.mem[addr + i] = 0
        return addr

    def allocate_string(self, val):
        """
        Allocates string in the heap segment and returns the start address.
        Appends the null terminator \0.
        """
        addr = self.heap_ptr
        size = len(val) + 1
        self.heap_ptr += size
        self.allocations[addr] = (size, 'char', 'string_literal', True, False, None)
        
        # Write characters
        for i, char in enumerate(val):
            self.mem[addr + i] = ord(char)
        self.mem[addr + len(val)] = 0  # Null terminator
        
        return addr

    def get_stack_ptr(self):
        return self.stack_ptr
    def deallocate_to_stack_ptr(self, ptr):
        """
        Removes all stack allocations with base_addr >= ptr.
        """
        to_remove = []
        for addr in self.allocations:
            # Stack allocations are in the 100000-500000 range.
            # We must ensure we don't accidentally remove global ( < 100000)
            # or heap ( >= 500000) allocations.
            if ptr <= addr < 500000: 
                to_remove.append(addr)

        for addr in to_remove:
            size, _, _, _, _, _ = self.allocations[addr]
            for i in range(size):
                if (addr + i) in self.mem:
                    del self.mem[addr + i]
            del self.allocations[addr]

        self.stack_ptr = ptr

    def deallocate_frame(self, frame_id, prev_stack_ptr=None):
        """
        Removes all stack allocations associated with frame_id.
        Optional prev_stack_ptr can be used to reset the stack pointer.
        """
        to_remove = []
        for addr, (size, type_name, name, is_array, is_pointer, f_id) in self.allocations.items():
            if f_id == frame_id:
                to_remove.append(addr)
                
        for addr in to_remove:
            size, _, _, _, _, _ = self.allocations[addr]
            for i in range(size):
                if (addr + i) in self.mem:
                    del self.mem[addr + i]
            del self.allocations[addr]
            
        if prev_stack_ptr is not None:
            self.stack_ptr = prev_stack_ptr

    def _find_allocation(self, addr):
        """
        Given a virtual address, find the allocation block it belongs to.
        Returns (base_addr, size, type_name, name, is_array, is_pointer, frame_id) or None.
        """
        for base_addr, (size, type_name, name, is_array, is_pointer, frame_id) in self.allocations.items():
            if base_addr <= addr < base_addr + size:
                return base_addr, size, type_name, name, is_array, is_pointer, frame_id
        return None

    def read(self, addr, line=None):
        if addr == 0:
            raise MemoryError("Null pointer dereference", line)
            
        alloc = self._find_allocation(addr)
        if not alloc:
            raise MemoryError(f"Segmentation fault: access to invalid memory address {addr}", line)
            
        return self.mem.get(addr, 0)

    def write(self, addr, val, line=None):
        if addr == 0:
            raise MemoryError("Null pointer dereference", line)
            
        alloc = self._find_allocation(addr)
        if not alloc:
            raise MemoryError(f"Segmentation fault: write to invalid memory address {addr}", line)
            
        base_addr, size, type_name, name, is_array, is_pointer, frame_id = alloc
        
        # Apply type casting/limits:
        # Pointers are always treated as word-sized (int)
        if is_pointer:
            val = ((val + 2**31) % 2**32) - 2**31
        elif type_name == 'char':
            val = ((val + 128) % 256) - 128
        elif type_name == 'int':
            val = ((val + 2**31) % 2**32) - 2**31
            
        self.mem[addr] = val

    def read_string(self, addr, line=None):
        """
        Helper to read a null-terminated string from memory.
        """
        chars = []
        curr = addr
        while True:
            ch_val = self.read(curr, line)
            if ch_val == 0:
                break
            chars.append(chr(ch_val))
            curr += 1
        return "".join(chars)

    def write_string(self, addr, py_str, line=None):
        """
        Helper to write a string into memory at target address.
        Does not perform safety check for buffer size, but checks address validity.
        """
        curr = addr
        for ch in py_str:
            self.write(curr, ord(ch), line)
            curr += 1
        self.write(curr, 0, line) # Null terminator

    def dump_vars(self):
        """
        Returns a list of strings representing all variables and their values.
        """
        res = []
        # Sort by base address to list logically
        for base_addr in sorted(self.allocations.keys()):
            size, type_name, name, is_array, is_pointer, frame_id = self.allocations[base_addr]
            if name == 'string_literal':
                continue
            
            scope_str = "global" if frame_id is None else f"local(frame {frame_id})"
            
            if is_array:
                # Print array contents up to 10 elements
                vals = []
                limit = min(size, 10)
                for i in range(limit):
                    vals.append(str(self.mem.get(base_addr + i, 0)))
                val_str = ", ".join(vals)
                if size > 10:
                    val_str += ", ..."
                res.append(f"{scope_str} {type_name} {name}[{size}] = {{{val_str}}}")
            else:
                val = self.mem.get(base_addr, 0)
                if type_name == 'char':
                    res.append(f"{scope_str} char {name} = {val} ('{chr(val) if 32 <= val <= 126 else '\\\\0'}')")
                elif type_name == 'int*':
                    res.append(f"{scope_str} int* {name} = {val}")
                elif type_name == 'char*':
                    res.append(f"{scope_str} char* {name} = {val}")
                else:
                    res.append(f"{scope_str} {type_name} {name} = {val}")
        return res
