import sys
import tkinter as tk
import uuid

# --- Grey Library (Tkinter-based) ---
class GreyLibrary:
    """A simplified Tkinter wrapper to emulate a GUI framework."""
    class GRC:
        """Represents a main window."""
        def __init__(self):
            self.root = tk.Tk()
            self._title = "TurboSwift Window"
            self._width = 400
            self._height = 300
            self.root.geometry(f"{self._width}x{self._height}")
            self.label = None

        @property
        def title(self):
            return self._title
        
        @title.setter
        def title(self, val):
            self._title = val
            self.root.title(val)

        @property
        def width(self):
            return self._width
        
        @width.setter
        def width(self, val):
            self._width = val
            self.root.geometry(f"{self._width}x{self._height}")

        @property
        def height(self):
            return self._height
        
        @height.setter
        def height(self, val):
            self._height = val
            self.root.geometry(f"{self._width}x{self._height}")

        def show(self):
            if self.label:
                self.label.pack()
            self.root.mainloop()

    class Label:
        """Represents a text label widget."""
        def __init__(self, parent, text=""):
            self.widget = tk.Label(parent.root, text=text)

        def pack(self):
            self.widget.pack()

# --- Lexer ---
def tokenize(code):
    """
    Splits the source code into a list of tokens.
    Handles identifiers, symbols, and string literals.
    """
    tokens = []
    current = ""
    # Add '>' to symbols for the '->' token
    symbols = '{}():=,+-.;>'
    i = 0
    while i < len(code):
        c = code[i]
        if c.isspace():
            if current:
                tokens.append(current)
                current = ""
            i += 1
            continue
        if c in symbols:
            if current:
                tokens.append(current)
                current = ""
            # Handle multi-character symbols like '->'
            if c == '-' and i + 1 < len(code) and code[i + 1] == '>':
                tokens.append('->')
                i += 2
                continue
            tokens.append(c)
            i += 1
            continue
        if c == '"':
            i += 1
            s = ""
            while i < len(code) and code[i] != '"':
                s += code[i]
                i += 1
            i += 1
            tokens.append(f'"{s}"')
            continue
        current += c
        i += 1
    if current:
        tokens.append(current)
    return tokens

# --- AST ---
class Contract:
    """Represents a contract/class in TurboSwift."""
    def __init__(self, name):
        self.name = name
        self.vars = {}
        self.methods = {}
        self.imports = {}

class Func:
    """Represents a function in TurboSwift."""
    def __init__(self, name, params):
        self.name = name
        self.params = params
        self.body = []

# --- Turbalance: Static Analysis ---
def turbalance_check(code):
    """Performs a simple static analysis for brace and syntax errors."""
    errors = []
    lines = code.splitlines()
    brace_stack = []
    for i, line in enumerate(lines, 1):
        for c in line:
            if c == '{':
                brace_stack.append(i)
            elif c == '}':
                if not brace_stack:
                    errors.append(f"[TURBALANCE] Line {i}: Extra '}}'")
                else:
                    brace_stack.pop()
        if line.strip().startswith("contract") and "{" not in line:
            errors.append(f"[TURBALANCE] Line {i}: Expected '{{' after 'contract'")
        if "func" in line and "(" not in line:
            errors.append(f"[TURBALANCE] Line {i}: Expected '(' after 'func'")
        if line.strip().startswith("import") and "aka" in line and not line.endswith(";"):
            errors.append(f"[TURBALANCE] Line {i}: Import statement must end with ';'")
    if brace_stack:
        for lnum in brace_stack:
            errors.append(f"[TURBALANCE] Line {lnum}: Unclosed '{{'")
    return errors

# --- Parser ---
def parse(tokens):
    """Parses the tokens into an Abstract Syntax Tree (AST)."""
    i = 0
    contracts = {}

    def expect(t):
        nonlocal i
        if i >= len(tokens) or tokens[i] != t:
            raise SyntaxError(f"Expected '{t}' at token {i}, got '{tokens[i] if i < len(tokens) else 'EOF'}'")
        i += 1

    def parse_import():
        nonlocal i
        i += 1
        if i >= len(tokens):
            raise SyntaxError("Unexpected EOF while parsing import")
        module_name = tokens[i]
        i += 1
        if i < len(tokens) and tokens[i] == "aka":
            i += 1
            if i >= len(tokens):
                raise SyntaxError("Unexpected EOF after 'aka'")
            alias = tokens[i]
            i += 1
            expect(";")
            return module_name, alias
        raise SyntaxError(f"Expected 'aka' after import at token {i}")

    def parse_contract():
        nonlocal i
        i += 1
        if i >= len(tokens):
            raise SyntaxError("Unexpected EOF while parsing contract name")
        name = tokens[i]
        i += 1
        expect("{")
        contract = Contract(name)
        while i < len(tokens) and tokens[i] != "}":
            if tokens[i] == "import":
                module_name, alias = parse_import()
                contract.imports[alias] = module_name
            elif tokens[i] in ("public", "private"):
                access = tokens[i]
                i += 1
                if i >= len(tokens):
                    raise SyntaxError("Unexpected EOF after access specifier")
                if tokens[i] == "var":
                    i += 1
                    varname = tokens[i]
                    i += 1
                    if i < len(tokens) and tokens[i] == ":":
                        i += 1
                        vartype = tokens[i]
                        i += 1
                    else:
                        vartype = "Unknown"
                    contract.vars[varname] = {"access": access, "type": vartype, "value": None}
                    if i < len(tokens) and tokens[i] == ";":
                        i += 1
                elif tokens[i] == "func":
                    i += 1
                    funcname = tokens[i]
                    i += 1
                    expect("(")
                    params = []
                    while i < len(tokens) and tokens[i] != ")":
                        if tokens[i] != ",":
                            params.append(tokens[i])
                        i += 1
                    expect(")")
                    rettype = "Void"
                    if i < len(tokens) and tokens[i] == "->":
                        i += 1
                        rettype = tokens[i]
                        i += 1
                    expect("{")
                    body = []
                    brace_count = 1
                    while i < len(tokens) and brace_count > 0:
                        if tokens[i] == "{":
                            brace_count += 1
                        elif tokens[i] == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                break
                        body.append(tokens[i])
                        i += 1
                    expect("}")
                    func = Func(funcname, params)
                    func.body = body
                    contract.methods[funcname] = func
                else:
                    i += 1
            else:
                i += 1
        expect("}")
        return contract

    while i < len(tokens):
        if tokens[i] == "contract":
            c = parse_contract()
            contracts[c.name] = c
        elif tokens[i] == "import":
            parse_import()
        else:
            i += 1
    return contracts

# --- TurboSwift Objects ---
class TurboSwiftObject:
    """
    A wrapper class for Python objects, allowing the interpreter to
    store and call methods on them.
    """
    def __init__(self, contract=None, py_obj=None):
        self.contract = contract
        self.fields = {}
        self.py_obj = py_obj

    def set_attr(self, name, value):
        self.fields[name] = value
        if self.py_obj:
            setattr(self.py_obj, name, value)

    def get_attr(self, name):
        if name in self.fields:
            return self.fields[name]
        if self.py_obj:
            return getattr(self.py_obj, name, None)
        return None

    def call(self, method_name, *args):
        if self.py_obj:
            # Check if the Python object has a setter for this property
            if hasattr(type(self.py_obj), method_name):
                # The user's code expects a method call for property setters, e.g., win.title("...").
                # This handles that by setting the attribute directly.
                if len(args) == 1:
                    setattr(self.py_obj, method_name, args[0])
                    return
            
            method = getattr(self.py_obj, method_name, None)
            if callable(method):
                return method(*args)
            else:
                raise Exception(f"Method '{method_name}' not found on Python object")
        
        # Fallback to internal contract methods
        if not self.contract:
            raise Exception("No contract for method call")
        if method_name not in self.contract.methods:
            raise Exception(f"Method '{method_name}' not found in contract '{self.contract.name}'")
        method = self.contract.methods[method_name]
        return execute_method(self, method)

# --- Execute Method ---
def execute_method(obj, method):
    """
    The core interpreter function that executes the body of a method.
    This has been significantly refactored to handle constructor calls
    and method calls with arguments.
    """
    body = method.body
    i = 0
    while i < len(body):
        token = body[i]

        # Handle constructor calls, e.g., `let window = grey.GRC();`
        if token == "let" and i + 6 < len(body) and body[i + 2] == "=" and body[i + 4] == "." and body[i + 5] == "(" and body[i + 6] == ")":
            var_name = body[i + 1]
            module_alias = body[i + 3]
            class_name = body[i + 5]
            
            module_obj = obj.get_attr(module_alias)
            if module_obj:
                # Get the Python class from the parent object
                py_class = module_obj.get_attr(class_name)
                if callable(py_class):
                    new_py_obj = py_class()
                    new_ts_obj = TurboSwiftObject(py_obj=new_py_obj)
                    obj.set_attr(var_name, new_ts_obj)
                    i += 7
                    continue
                else:
                    raise TypeError(f"'{class_name}' is not a callable class.")
            else:
                raise NameError(f"Module '{module_alias}' not found.")
        
        # Handle method calls with arguments, e.g., `window.title("Hello");`
        if i + 3 < len(body) and body[i + 1] == "." and body[i + 3] == "(":
            obj_name = body[i]
            method_name = body[i + 2]
            called_obj = obj.get_attr(obj_name)
            
            if called_obj:
                args = []
                arg_start_idx = i + 4
                arg_end_idx = arg_start_idx
                while arg_end_idx < len(body) and body[arg_end_idx] != ")":
                    arg_end_idx += 1
                
                # Parse arguments
                arg_tokens = body[arg_start_idx:arg_end_idx]
                for arg_token in arg_tokens:
                    if arg_token == ",": continue
                    if arg_token.startswith('"') and arg_token.endswith('"'):
                        args.append(arg_token.strip('"'))
                    elif arg_token.isdigit():
                        args.append(int(arg_token))
                    else:
                        args.append(obj.get_attr(arg_token))
                
                called_obj.call(method_name, *args)
                i = arg_end_idx + 2 # Skip past ')' and ';'
                continue

        # Handle simple print statement, e.g., `print("Hello");` or `print(myVar);`
        if token == "print" and i + 3 < len(body) and body[i+1] == "(" and body[i+3] == ")":
            val_token = body[i+2]
            if val_token.startswith('"') and val_token.endswith('"'):
                print(val_token.strip('"'))
            else:
                # Look up the variable and print its value
                var_value = obj.get_attr(val_token)
                print(var_value)
            i += 4
            continue

        # Simple variable assignment, e.g., `let x = "Hello";`
        if token == "let" and i + 3 < len(body) and body[i+2] == "=":
            var_name = body[i+1]
            value_token = body[i+3]
            
            value = None
            if value_token.startswith('"') and value_token.endswith('"'):
                value = value_token.strip('"')
            elif value_token.isdigit():
                value = int(value_token)
            else:
                value = obj.get_attr(value_token)
            
            obj.set_attr(var_name, value)
            i += 4
            continue
        
        # Move to the next token
        i += 1
    return None

# --- Main Function ---
def main():
    """Main function to run the TurboSwift compiler."""
    if len(sys.argv) < 3:
        print("Usage: turboswift run <file>")
        return
    cmd = sys.argv[1]
    if cmd != "run":
        print("Unknown command. Use: turboswift run <file>")
        return
    filename = sys.argv[2]
    try:
        with open(filename, encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return

    errors = turbalance_check(code)
    if errors:
        for err in errors:
            print(err)
        print("Fix errors before running.")
        return

    tokens = tokenize(code)
    try:
        contracts = parse(tokens)
    except SyntaxError as e:
        print(f"Parsing error: {e}")
        return

    if "App" not in contracts:
        print("Contract App not found")
        return
    app_contract = contracts["App"]
    if "main" not in app_contract.methods:
        print("Function main not found in contract App")
        return

    # Correctly initialize the 'grey' object with the GreyLibrary classes
    grey_obj = TurboSwiftObject()
    grey_obj.set_attr("GRC", GreyLibrary.GRC)
    grey_obj.set_attr("Label", GreyLibrary.Label)

    app_obj = TurboSwiftObject(contract=app_contract)
    if "grey" in app_contract.imports and app_contract.imports["grey"] == "grey":
        app_obj.set_attr("grey", grey_obj)
    else:
        print("Warning: 'import grey aka grey;' not found in contract App")
    
    # Execute the main function from the App contract
    app_obj.call("main")

if __name__ == "__main__":
    main()
