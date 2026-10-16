# backend/cross_language_auditor.py

import re


def analyze_cross_language_code(source_code: str, language: str, filename: str = "source") -> dict:
    """
    Performs lexical and pattern-based static analysis on non-Python source files
    (JavaScript, TypeScript, Java, etc.) using simple English messages.
    """
    lang = (language or "").lower()
    forensic_flags = []
    structured_flags = []

    # 1. Function / Method Counting
    function_count = 0
    if lang in ["javascript", "js", "ts", "typescript"]:
        func_matches = re.findall(
            r'\bfunction\s+[a-zA-Z0-9_$]+\s*\(|\b(?:const|let|var)\s+[a-zA-Z0-9_$]+\s*=\s*(?:async\s*)?\(.*?\)\s*=>',
            source_code
        )
        function_count = len(func_matches)
    elif lang in ["java", "csharp", "cpp", "c++"]:
        method_matches = re.findall(
            r'\b(public|private|protected|static|\s)+[\w<>\[\]]+\s+[a-zA-Z0-9_$]+\s*\(.*?\)\s*(?:throws\s+[^{]+)?\s*\{',
            source_code
        )
        function_count = len(method_matches)

    if function_count == 0:
        function_count = source_code.lower().count("function") + source_code.lower().count("public ")

    # 2. Hardcoded Secrets Detection
    secret_patterns = [
        r'\b(secret|password|api_key|apikey|auth_token|access_token)\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{8,}["\']',
    ]
    for pattern in secret_patterns:
        match = re.search(pattern, source_code, re.IGNORECASE)
        if match:
            line_no = source_code[:match.start()].count("\n") + 1
            msg = f"A password or secret key appears to be written directly inside {filename} on line {line_no}."
            forensic_flags.append(msg)
            structured_flags.append({
                "severity": "CRITICAL",
                "category": f"Exposed Password or Secret Key ({filename})",
                "line": f"Line {line_no}",
                "message": msg
            })
            break

    # 3. Dangerous eval() in JS/TS
    if lang in ["javascript", "js", "ts", "typescript"] and re.search(r'\beval\s*\(', source_code):
        msg = f"Uses 'eval()' inside {filename}, which can be unsafe in JavaScript/TypeScript."
        forensic_flags.append(msg)
        structured_flags.append({
            "severity": "CRITICAL",
            "category": f"Unsafe Code Command ({filename})",
            "line": "Line 1",
            "message": msg
        })

    # 4. Documentation / Comment Checks
    has_docs = False
    if lang in ["javascript", "js", "ts", "typescript", "java"]:
        if "/**" in source_code or "//" in source_code or "/*" in source_code:
            has_docs = True

    if not has_docs and function_count > 0:
        msg = f"File '{filename}' has {function_count} function(s) but no helpful code comments explaining how it works."
        forensic_flags.append(msg)
        structured_flags.append({
            "severity": "WARNING",
            "category": f"No Code Comments ({filename})",
            "line": "Code Style",
            "message": msg
        })

    complexity_score = (
        source_code.count("if") +
        source_code.count("for") +
        source_code.count("while") +
        source_code.count("switch") +
        source_code.count("catch")
    )

    return {
        "language": language,
        "syntax_valid": True,
        "function_count": function_count,
        "class_count": source_code.lower().count("class "),
        "ast_node_complexity": complexity_score + function_count,
        "forensic_flags": forensic_flags,
        "structured_flags": structured_flags
    }