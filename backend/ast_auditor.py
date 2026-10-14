# backend/ast_auditor.py

import ast

def analyze_python_code_structure(code_content: str) -> dict:
    """
    Parses Python code using AST to extract imported modules and 
    return structured forensic flags with severity levels, categories, and line numbers.
    """
    imported_modules = []
    forensic_flags = []
    
    try:
        tree = ast.parse(code_content)
        for node in ast.walk(tree):
            # Track module imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)
            
            # Forensic Check: Detect dangerous built-in functions
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    forensic_flags.append({
                        "severity": "CRITICAL",
                        "category": "Security Vulnerability",
                        "message": f"Use of unsafe built-in function '{node.func.id}' detected.",
                        "line": node.lineno
                    })
                    
        # If no security issues found, add a clean informational notice
        if not any(f.get("severity") == "CRITICAL" for f in forensic_flags):
            forensic_flags.append({
                "severity": "INFO",
                "category": "Code Quality",
                "message": "AST code structure parsed successfully with no critical security flags.",
                "line": 1
            })
            
    except SyntaxError as se:
        forensic_flags.append({
            "severity": "CRITICAL",
            "category": "Syntax Error",
            "message": str(se),
            "line": se.lineno or 1
        })
    except Exception as e:
        forensic_flags.append({
            "severity": "WARNING",
            "category": "Parsing Warning",
            "message": str(e),
            "line": 1
        })
        
    return {
        "imported_modules": list(set(imported_modules)),
        "forensic_flags": forensic_flags
    }