import sys
from repl import REPL

def main():
    repl = REPL()
    
    # If a file argument is provided on startup, run it and exit
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        print(f"Executing script '{filename}'...")
        repl.buffer = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                repl.buffer = [line.rstrip('\r\n') for line in f]
            repl.current_file = filename
            repl.modified = False
            success = repl.handle_compile(execute=True)
            sys.exit(0 if success else 1)
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error executing file: {e}")
            sys.exit(1)
    else:
        # Start interactive REPL mode
        repl.run()

if __name__ == '__main__':
    main()
