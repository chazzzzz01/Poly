# To understand how this code work understand each code do some research on it.
# recommeded to copy each code then make chatgpt explain each code and syntax how it work.
# Be sure to understand regix patterns use in the code.
# Do some research on each code block to understand it.


import re
import io
import contextlib

class PolyLangInterpreter:
    def __init__(self):
        self.context = {}

    
    # Expression Evaluator
    
    def eval_expr(self, expr, ctx):
        expr = expr.strip()
        # Inline if-then-else
        m = re.match(r'if (.+) then (.+) else (.+)', expr)
        if m:
            cond, true_expr, false_expr = m.groups()
            expr = f"({true_expr}) if ({cond}) else ({false_expr})"

        try:
            return eval(expr, {}, ctx)
        except Exception:
            return expr

    
    #Function Maker (supports closure + recursion)
    
    def make_func(self, args, body, outer_ctx, name=None):
        """
        Create a Python-callable that supports:
         - closures
         - recursion
         - nested function literals
        """
        def f(*passed_args):
            local_ctx = dict(zip(args, passed_args))
            combined_ctx = {**outer_ctx, **self.context, **local_ctx}

            if name:
                combined_ctx[name] = f  

            body_strip = body.strip()

            # Nested function literal (closure)
            nested_match = re.match(r'func\s*\((.*?)\)\s*=\s*(.+)', body_strip)
            if nested_match:
                inner_args_str, inner_body = nested_match.groups()
                inner_args = [a.strip() for a in inner_args_str.split(',') if a.strip()]
                return self.make_func(inner_args, inner_body, combined_ctx)

            try:
                return eval(body_strip, {}, combined_ctx)
            except Exception:
                return self.eval_expr(body_strip, combined_ctx)

        return f

   
    # Line Parser
   
    def parse_line(self, line, output_buffer=None):
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        # PRINT STATEMENT (with optional / for space)
        if line.startswith("print(") and (line.endswith(")") or line.endswith("/)")):
            add_space = line.endswith("/)")  # check if it ends with /)
            expr = line[6:-2].strip() if add_space else line[6:-1].strip()

            # simple variable interpolation
            expr = re.sub(
                r'{(\w+)}',
                lambda m: str(self.context.get(m.group(1), m.group(0))),
                expr
            )

            try:
                value = self.eval_expr(expr, self.context)
            except Exception:
                value = expr

            if output_buffer and str(value).strip():
                output_buffer.write(str(value))
                if add_space:
                    output_buffer.write(" ")  # add space if print(.../) used
            return None

        # VARIABLE DECLARATION: let x = ...
        if line.startswith("let "):
            m = re.match(r'let (\w+)\s*=\s*(.+)', line)
            if m:
                var, expr = m.groups()
                expr = expr.strip()

                # Function literal assigned to variable (closure)
                func_def = re.match(r'func\s*\((.*?)\)\s*=\s*(.+)', expr)
                if func_def:
                    args_str, body = func_def.groups()
                    args = [a.strip() for a in args_str.split(',') if a.strip()]
                    self.context[var] = self.make_func(args, body, dict(self.context))
                    return None

                # Function call assigned to variable
                func_call = re.match(r'(\w+)\((.*?)\)', expr)
                if func_call:
                    func_name, args_str = func_call.groups()
                    func_obj = self.context.get(func_name)
                    if callable(func_obj):
                        args_list = [
                            self.eval_expr(a.strip(), self.context)
                            for a in args_str.split(',') if a.strip()
                        ]
                        self.context[var] = func_obj(*args_list)
                        return None

                # Regular variable assignment
                try:
                    self.context[var] = self.eval_expr(expr, self.context)
                except Exception:
                    self.context[var] = expr
            return None

        # FUNCTION DEFINITION: func name(a,b)= body
        m = re.match(r'func (\w+)\((.*?)\)\s*=\s*(.+)', line)
        if m:
            name, args_str, body = m.groups()
            args = [a.strip() for a in args_str.split(',') if a.strip()]
            self.context[name] = self.make_func(args, body, dict(self.context), name)
            return None

        # FUNCTION CALL (standalone)
        func_call = re.match(r'(\w+)\((.*?)\)', line)
        if func_call:
            name, args_str = func_call.groups()
            func_obj = self.context.get(name)
            if callable(func_obj):
                args_list = [
                    self.eval_expr(a.strip(), self.context)
                    for a in args_str.split(',') if a.strip()
                ]
                result = func_obj(*args_list)
                if result is not None and output_buffer:
                    output_buffer.write(str(result))
                return result

        return None

    
    #Code Runner
    
    def run(self, code):
        code = code.strip()
        if not code:
            return ""

        lines = code.split("\n")
        output_buffer = io.StringIO()
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # IF-ELSE BLOCK
            if line.startswith("if ") and " then" in line:
                condition = line[3:line.index("then")].strip()
                try:
                    cond_result = eval(condition, {}, self.context)
                except Exception:
                    cond_result = False

                true_block, false_block = [], []
                i += 1

                while i < len(lines):
                    curr = lines[i].strip()
                    if curr.startswith("else:"):
                        i += 1
                        break
                    if curr:
                        true_block.append(curr)
                    i += 1

                while i < len(lines):
                    curr = lines[i].strip()
                    if not curr or curr.startswith(("if ", "let ", "func ")):
                        i -= 1
                        break
                    false_block.append(curr)
                    i += 1

                block_to_run = true_block if cond_result else false_block
                for stmt in block_to_run:
                    self.parse_line(stmt, output_buffer)

            else:
                self.parse_line(line, output_buffer)

            i += 1

        return output_buffer.getvalue().strip()


