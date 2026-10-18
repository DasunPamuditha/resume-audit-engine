# backend/cross_language_auditor.py

import re
from typing import Dict, List, Any


def analyze_cross_language_code(source_code: str, language: str, filename: str = "source") -> dict:
    """
    Performs line-by-line lexical and stylometric coding pattern analysis on JavaScript,
    TypeScript, and Java files to detect mixed authorship or copy-pasted code patterns.
    """
    lang = (language or "").lower()
    forensic_flags = []
    structured_flags = []

    # 1. Line-by-Line Indentation & Semicolon Habit Check
    lines = source_code.splitlines()
    tab_lines = []
    space_2_lines = []
    space_4_lines = []
    semicolon_lines = []
    no_semicolon_lines = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "/*", "*", "import ", "export ")):
            continue

        leading = line[:len(line) - len(line.lstrip())]
        if leading:
            if "\t" in leading:
                tab_lines.append(idx)
            elif " " in leading:
                scount = len(leading)
                if scount % 4 == 0:
                    space_4_lines.append(idx)
                elif scount % 2 == 0:
                    space_2_lines.append(idx)

        # Semicolon habit check for statement lines in JS/TS
        if lang in ["javascript", "js", "ts", "typescript"]:
            if re.match(r"^(const|let|var|return)\s+.+", stripped) and not stripped.endswith(("{", "(", ",", "[")):
                if stripped.endswith(";"):
                    semicolon_lines.append(idx)
                else:
                    no_semicolon_lines.append(idx)

    if tab_lines and (space_2_lines or space_4_lines):
        space_ex = (space_2_lines or space_4_lines)[0]
        msg = (
            f"File '{filename}' mixes Tab indentation (Line {tab_lines[0]}) and Space indentation "
            f"(Line {space_ex}), which often happens when code is pasted from different sources."
        )
        forensic_flags.append(msg)
        structured_flags.append({
            "severity": "WARNING",
            "category": f"Inconsistent Indentation Pattern ({filename})",
            "line": f"Lines {tab_lines[0]}, {space_ex}",
            "message": msg
        })

    if len(semicolon_lines) >= 3 and len(no_semicolon_lines) >= 3:
        msg = (
            f"File '{filename}' switches between using semicolons ';' (e.g. Line {semicolon_lines[0]}) and "
            f"omitting semicolons (e.g. Line {no_semicolon_lines[0]}), showing mixed coding habits."
        )
        forensic_flags.append(msg)
        structured_flags.append({
            "severity": "WARNING",
            "category": f"Inconsistent Semicolon Pattern ({filename})",
            "line": f"Lines {semicolon_lines[0]}, {no_semicolon_lines[0]}",
            "message": msg
        })

    # 2. Function / Method Counting & Naming Stylometry with Line Numbers
    function_count = 0
    naming_examples: Dict[str, List[str]] = {"snake_case": [], "camelCase": [], "PascalCase": []}

    for idx, line in enumerate(lines, start=1):
        if lang in ["javascript", "js", "ts", "typescript"]:
            m = re.search(
                r'\bfunction\s+([a-zA-Z0-9_$]+)\s*\(|\b(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>',
                line
            )
            if m:
                function_count += 1
                fname = m.group(1) or m.group(2)
                if fname and len(fname) >= 3:
                    if "_" in fname and fname.lower() == fname:
                        naming_examples["snake_case"].append(f"'{fname}' (Line {idx})")
                    elif re.search(r"^[a-z][a-zA-Z0-9]*[A-Z]", fname):
                        naming_examples["camelCase"].append(f"'{fname}' (Line {idx})")
                    elif re.search(r"^[A-Z][a-zA-Z0-9]*[a-z]", fname):
                        naming_examples["PascalCase"].append(f"'{fname}' (Line {idx})")
        elif lang in ["java", "csharp", "cpp", "c++"]:
            m = re.search(
                r'\b(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+([a-zA-Z0-9_$]+)\s*\(',
                line
            )
            if m:
                fname = m.group(1)
                if fname and fname not in ["if", "for", "while", "switch", "catch"]:
                    function_count += 1
                    if "_" in fname:
                        naming_examples["snake_case"].append(f"'{fname}' (Line {idx})")
                    elif re.search(r"^[a-z][a-zA-Z0-9]*[A-Z]", fname):
                        naming_examples["camelCase"].append(f"'{fname}' (Line {idx})")

    if function_count == 0:
        function_count = source_code.lower().count("function") + source_code.lower().count("public ")

    # Check for mixed snake_case and camelCase in the same file
    if naming_examples["snake_case"] and naming_examples["camelCase"]:
        s_ex = naming_examples["snake_case"][0]
        c_ex = naming_examples["camelCase"][0]
        msg = (
            f"File '{filename}' mixes different function naming patterns: snake_case ({s_ex}) and "
            f"camelCase ({c_ex}). This suggests multiple people wrote or pasted code into this file."
        )
        forensic_flags.append(msg)
        structured_flags.append({
            "severity": "WARNING",
            "category": f"Mixed Coding Naming Pattern ({filename})",
            "line": "Code Pattern Shift",
            "message": msg
        })

    # 3. Hardcoded Secrets Detection
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

    # 4. Dangerous eval() in JS/TS
    if lang in ["javascript", "js", "ts", "typescript"] and re.search(r'\beval\s*\(', source_code):
        msg = f"Uses 'eval()' inside {filename}, which can be unsafe in JavaScript/TypeScript."
        forensic_flags.append(msg)
        structured_flags.append({
            "severity": "CRITICAL",
            "category": f"Unsafe Code Command ({filename})",
            "line": "Line 1",
            "message": msg
        })

    # 5. Documentation / Comment Checks
    has_docs = False
    if lang in ["javascript", "js", "ts", "typescript", "java"]:
        if "/**" in source_code or "//" in source_code or "/*" in source_code:
            has_docs = True

    if not has_docs and function_count > 2:
        msg = f"File '{filename}' has {function_count} functions/methods but zero code comments explaining the logic."
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

    dominant_naming = "snake_case" if len(naming_examples["snake_case"]) > len(naming_examples["camelCase"]) else "camelCase"
    dominant_indent = "tabs" if len(tab_lines) > (len(space_2_lines) + len(space_4_lines)) else (
        "4-space" if len(space_4_lines) > len(space_2_lines) else "2-space"
    )

    style_signature = {
        "language": lang,
        "filename": filename,
        "naming_convention": dominant_naming,
        "indentation": dominant_indent,
        "semicolon_style": "omit" if len(no_semicolon_lines) > len(semicolon_lines) else "always"
    }

    return {
        "language": language,
        "syntax_valid": True,
        "function_count": function_count,
        "class_count": source_code.lower().count("class "),
        "ast_node_complexity": complexity_score + function_count,
        "forensic_flags": forensic_flags,
        "structured_flags": structured_flags,
        "style_signature": style_signature
    }