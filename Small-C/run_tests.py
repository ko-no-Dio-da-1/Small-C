import os
import sys
import subprocess

def run_tests():
    # Find all .sc files in current directory
    sc_files = [f for f in os.listdir('.') if f.endswith('.sc')]
    sc_files.sort()
    
    if not sc_files:
        print("No .sc test files found.")
        return
        
    passed_count = 0
    failed_count = 0
    
    print(f"Starting execution of {len(sc_files)} Small-C tests...")
    print("-" * 50)
    
    for sc_file in sc_files:
        expected_file = sc_file.rsplit('.', 1)[0] + '.expected'
        
        # Run test script
        cmd = [sys.executable, 'main.py', sc_file]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        
        # Read expected output
        if not os.path.exists(expected_file):
            print(f"[WARN] Expected file '{expected_file}' not found. Skipping validation.")
            continue
            
        with open(expected_file, 'r', encoding='utf-8') as f:
            expected_content = f.read()
            
        # Clean outputs (normalize line endings and whitespace)
        actual = normalize_whitespace(res.stdout)
        expected = normalize_whitespace(expected_content)
        
        # We need to strip standard Startup/Exit header lines from actual output if they are in test files
        # Let's clean the "Executing script 'filename'..." header line from actual output if present
        actual_lines = actual.strip().split('\n')
        if actual_lines and actual_lines[0].startswith("Executing script"):
            actual_lines = actual_lines[1:]
        actual = "\n".join(actual_lines).strip()
        expected = expected.strip()
        
        if actual == expected:
            print(f"[PASS] {sc_file}")
            passed_count += 1
        else:
            print(f"[FAIL] {sc_file}")
            print("--- EXPECTED ---")
            print(expected)
            print("--- ACTUAL ---")
            print(actual)
            print("-" * 50)
            failed_count += 1
            
    print("-" * 50)
    print(f"Results: {passed_count} Passed, {failed_count} Failed.")
    sys.exit(failed_count)

def normalize_whitespace(text):
    # Normalize Windows line endings and trim trailing spaces on each line
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()

if __name__ == '__main__':
    run_tests()
