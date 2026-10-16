# backend/ast_auditor.py

import ast
import re


def analyze_python_code_structure(code_content: str, filename: str = "source.py") -> dict:
    """
    Parses Python code using AST to extract imported modules and
    return structured forensic flags in simple, easy-to-understand English.
    """
    imported_modules = []
    forensic_flags = []

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

            # Forensic Check 1: Detect dangerous built-in functions (eval / exec)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    forensic_flags.append({
                        "severity": "CRITICAL",
                        "category": f"Unsafe Code Command ({filename})",
                        "message": f"Uses the '{node.func.id}()' command on line {node.lineno}, which can be a security risk.",
                        "line": f"Line {node.lineno}"
                    })

            # Forensic Check 2: Detect empty stub functions (placeholder / synthetic boilerplate)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    forensic_flags.append({
                        "severity": "WARNING",
                        "category": f"Empty Placeholder Function ({filename})",
                        "message": f"Function '{node.name}()' on line {node.lineno} is empty ('pass') with no working code inside.",
                        "line": f"Line {node.lineno}"
                    })

            # Forensic Check 3: Bare except clauses swallowing exceptions
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    forensic_flags.append({
                        "severity": "WARNING",
                        "category": f"Hidden Error Handling ({filename})",
                        "message": f"Line {node.lineno} uses a blank 'except:' block, which hides errors instead of handling them properly.",
                        "line": f"Line {node.lineno}"
                    })

        # Forensic Check 4: Hardcoded Secrets / API Keys via lexical scan
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

        # If no critical security issues found, add a clean informational notice
        if not any(f.get("severity") == "CRITICAL" for f in forensic_flags):
            forensic_flags.append({
                "severity": "INFO",
                "category": f"Clean Python Code ({filename})",
                "message": "Python code structure is valid and has no major security risks.",
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

    return {
        "imported_modules": list(set(imported_modules)),
        "forensic_flags": forensic_flags
    }