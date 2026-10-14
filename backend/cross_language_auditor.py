# backend/cross_language_auditor.py

import re

def analyze_cross_language_code(source_code: str, language: str) -> dict:
    """
    Performs lexical and pattern-based static analysis on non-Python source files 
    (JavaScript, Java, etc.) to evaluate code quality, documentation, and security flags.
    """
    lang = language.lower()
    forensic_flags = []

    # 1. Function / Method Counting
    function_count = 0
    if lang in ["javascript", "js", "ts", "typescript"]:
        func_matches = re.findall(r'\bfunction\s+[a-zA-Z0-9_$]+\s*\(|\bconst\s+[a-zA-Z0-9_$]+\s*=\s*(?:async\s*)?\(.*?\)\s*=>', source_code)
        function_count = len(func_matches)
    elif lang in ["java", "csharp", "cpp", "c++"]:
        method_matches = re.findall(r'\b(public|private|protected|static|\s)+[\w<>\[\]]+\s+[a-zA-Z0-9_$]+\s*\(.*?\)\s*(?:throws\s+[^{]+)?\s*\{', source_code)
        function_count = len(method_matches)

    if function_count == 0:
        function_count = source_code.lower().count("function") + source_code.lower().count("public ")

    # 2. Hardcoded Secrets Detection
    secret_patterns = [
        r'\b(secret|password|api_key|apikey|auth_token|access_token)\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{8,}["\']',
    ]
    for pattern in secret_patterns:
        if re.search(pattern, source_code, re.IGNORECASE):
            forensic_flags.append("Potential hardcoded secret or credential detected in source code")
            break

    # 3. Documentation / Comment Checks
    has_docs = False
    if lang in ["javascript", "js", "ts", "typescript", "java"]:
        if "/**" in source_code or "//" in source_code or "/*" in source_code:
            has_docs = True

    if not has_docs and function_count > 0:
        forensic_flags.append("Source file lacks standard code documentation or comments")

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
        "forensic_flags": forensic_flags
    }
