# backend/ast_auditor.py

import ast
import re
from typing import Dict, List, Any


def _classify_identifier_style(name: str) -> str:
    if not name or name.startswith("__") or name.isupper() or len(name) < 3:
        return "neutral"
    if "_" in name and name.lower() == name:
        return "snake_case"
    if re.search(r"^[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*$", name):
        return "camelCase"
    if re.search(r"^[A-Z][a-zA-Z0-9]*[a-z][a-zA-Z0-9]*$", name):
        return "PascalCase"
    return "neutral"


def analyze_python_code_structure(code_content: str, filename: str = "source.py") -> dict:
    """
    Parses Python code using AST and line-by-line stylometry to extract imported modules,
    check security, and detect inconsistent coding patterns across lines and functions.
    """
    imported_modules = []
    forensic_flags = []

    function_styles: Dict[str, List[str]] = {"snake_case": [], "camelCase": [], "PascalCase": []}
    variable_styles: Dict[str, List[str]] = {"snake_case": [], "camelCase": []}
    typed_functions = 0
    untyped_functions = 0

    # 1. Line-by-Line Indentation & Quote Pattern Analysis
    lines = code_content.splitlines()
    tab_indent_lines = []
    space_indent_lines = []
    indent_2_lines = []
    indent_4_lines = []
    single_quote_lines = 0
    double_quote_lines = 0

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check leading whitespace (Indentation pattern)
        leading = line[:len(line) - len(line.lstrip())]
        if leading:
            if "\t" in leading:
                tab_indent_lines.append(idx)
            elif " " in leading:
                space_indent_lines.append(idx)
                space_count = len(leading)
                if space_count % 4 == 0:
                    indent_4_lines.append(idx)
                elif space_count % 2 == 0:
                    indent_2_lines.append(idx)

        # Check quote style habits on code lines
        if "'" in stripped and '"' not in stripped:
            single_quote_lines += 1
        elif '"' in stripped and "'" not in stripped:
            double_quote_lines += 1

    # Flag mixed Tabs vs Spaces indentation in the same file
    if tab_indent_lines and space_indent_lines:
        forensic_flags.append({
            "severity": "WARNING",
            "category": f"Inconsistent Indentation Pattern ({filename})",
            "message": (
                f"File '{filename}' mixes Tab indentation (e.g. Line {tab_indent_lines[0]}) and Space indentation "
                f"(e.g. Line {space_indent_lines[0]}). This often happens when code lines are copied from another source."
            ),
            "line": f"Lines {tab_indent_lines[0]}, {space_indent_lines[0]}"
        })
    elif len(indent_2_lines) >= 3 and len(indent_4_lines) >= 3:
        forensic_flags.append({
            "severity": "WARNING",
            "category": f"Shifting Indentation Width ({filename})",
            "message": (
                f"File '{filename}' switches between 2-space indentation (Line {indent_2_lines[0]}) and "
                f"4-space indentation (Line {indent_4_lines[0]}), indicating mixed coding formatting."
            ),
            "line": f"Lines {indent_2_lines[0]}, {indent_4_lines[0]}"
        })

    # 2. AST Structural & Naming Pattern Inspection
    try:
        tree = ast.parse(code_content)
        for node in ast.walk(tree):
            # Track module imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module.split(".")[0])

            # Forensic Check: Dangerous built-in functions (eval / exec)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    forensic_flags.append({
                        "severity": "CRITICAL",
                        "category": f"Unsafe Code Command ({filename})",
                        "message": f"Uses the '{node.func.id}()' command on line {node.lineno}, which is a security risk.",
                        "line": f"Line {node.lineno}"
                    })

            # Function Naming & Type-Hint Stylometry
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    forensic_flags.append({
                        "severity": "WARNING",
                        "category": f"Empty Placeholder Function ({filename})",
                        "message": f"Function '{node.name}()' on line {node.lineno} is empty ('pass') with no working code inside.",
                        "line": f"Line {node.lineno}"
                    })

                style = _classify_identifier_style(node.name)
                if style in function_styles:
                    function_styles[style].append(f"'{node.name}' (Line {node.lineno})")

                has_type_hints = bool(node.returns) or any(arg.annotation is not None for arg in node.args.args)
                if has_type_hints:
                    typed_functions += 1
                else:
                    untyped_functions += 1

            # Variable Assignment Naming Stylometry
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        v_style = _classify_identifier_style(target.id)
                        if v_style in variable_styles:
                            variable_styles[v_style].append(f"'{target.id}' (Line {node.lineno})")

            # Bare except clauses
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    forensic_flags.append({
                        "severity": "WARNING",
                        "category": f"Hidden Error Handling ({filename})",
                        "message": f"Line {node.lineno} uses a blank 'except:' block, which hides errors instead of handling them properly.",
                        "line": f"Line {node.lineno}"
                    })

        # Flag Function Naming Style Shift within the same file
        if function_styles["snake_case"] and function_styles["camelCase"]:
            snake_ex = function_styles["snake_case"][0]
            camel_ex = function_styles["camelCase"][0]
            forensic_flags.append({
                "severity": "WARNING",
                "category": f"Mixed Function Naming Pattern ({filename})",
                "message": (
                    f"File '{filename}' mixes snake_case functions ({snake_ex}) with camelCase functions ({camel_ex}). "
                    f"Mixing naming styles in the same Python file suggests multiple authors or pasted code."
                ),
                "line": "Code Pattern Shift"
            })

        # Flag Variable Naming Style Shift within the same file
        if len(variable_styles["snake_case"]) >= 2 and len(variable_styles["camelCase"]) >= 2:
            snake_v = variable_styles["snake_case"][0]
            camel_v = variable_styles["camelCase"][0]
            forensic_flags.append({
                "severity": "WARNING",
                "category": f"Mixed Variable Naming Pattern ({filename})",
                "message": (
                    f"Variables in '{filename}' switch between snake_case ({snake_v}) and camelCase ({camel_v}), "
                    f"showing inconsistent coding habits across lines."
                ),
                "line": "Variable Pattern Shift"
            })

        # Hardcoded Secrets / API Keys via lexical scan
        secret_match = re.search(
            r'\b(secret|password|api_key|apikey|auth_token|access_token)\s*=\s*["\'][a-zA-Z0-9_\-\.]{8,}["\']',
            code_content,
            re.IGNORECASE
        )
        if secret_match:
            line_num = code_content[:secret_match.start()].count("\n") + 1
            forensic_flags.append({
                "severity": "CRITICAL",
                "category": f"Exposed Password or API Key ({filename})",
                "message": f"A password or secret API key appears to be written directly inside the code on line {line_num}.",
                "line": f"Line {line_num}"
            })

        if not any(f.get("severity") in ["CRITICAL", "WARNING"] for f in forensic_flags):
            forensic_flags.append({
                "severity": "INFO",
                "category": f"Consistent Python Coding Pattern ({filename})",
                "message": "Python code structure and line-by-line naming patterns are consistent and clean.",
                "line": "Verified"
            })

    except SyntaxError as se:
        forensic_flags.append({
            "severity": "CRITICAL",
            "category": f"Broken Python Syntax ({filename})",
            "message": f"This Python file has a syntax error on line {se.lineno or 1}: {se.msg}",
            "line": f"Line {se.lineno or 1}"
        })
    except Exception as e:
        forensic_flags.append({
            "severity": "WARNING",
            "category": f"Code Check Note ({filename})",
            "message": str(e),
            "line": "Line 1"
        })

    # Build a style signature so ResumeAuditor can compare coding patterns across repositories
    dominant_naming = (
        "camelCase"
        if len(function_styles["camelCase"]) + len(variable_styles["camelCase"])
        > len(function_styles["snake_case"]) + len(variable_styles["snake_case"])
        else "snake_case"
    )
    dominant_indent = "tabs" if len(tab_indent_lines) > len(space_indent_lines) else (
        "2-space" if len(indent_2_lines) > len(indent_4_lines) else "4-space"
    )
    dominant_quotes = "single-quotes" if single_quote_lines > double_quote_lines else "double-quotes"

    style_signature = {
        "language": "python",
        "filename": filename,
        "naming_convention": dominant_naming,
        "indentation": dominant_indent,
        "quote_style": dominant_quotes,
        "uses_type_hints": typed_functions > untyped_functions
    }

    return {
        "imported_modules": list(set(imported_modules)),
        "forensic_flags": forensic_flags,
        "style_signature": style_signature
    }