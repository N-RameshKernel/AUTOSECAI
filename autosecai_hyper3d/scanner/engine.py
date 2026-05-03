"""Transparent vulnerability scanner used by the AutoSecAI prototype.

The engine intentionally starts with deterministic rules so the demo is
explainable. It can later become the normalization layer in front of CodeQL,
Tree-sitter, Semgrep, or an LLM remediation service.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
import hashlib
import re
from typing import Iterable


SEVERITY_WEIGHT = {
    "Critical": 45,
    "High": 35,
    "Medium": 22,
    "Low": 10,
}


@dataclass(frozen=True)
class Rule:
    type: str
    severity: str
    cwe: str
    owasp: str
    patterns: tuple[re.Pattern[str], ...]
    explanation: str
    fix: str
    secure_example: str
    learning: str


def _compile(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


RULES: tuple[Rule, ...] = (
    Rule(
        type="SQL Injection",
        severity="High",
        cwe="CWE-89",
        owasp="A03:2021 Injection",
        patterns=_compile(
            r"\bSELECT\b.+\bFROM\b.+(\+|%|\.format\(|f[\"'])",
            r"\b(INSERT|UPDATE|DELETE)\b.+(\+|%|\.format\(|f[\"'])",
            r"\bexecute\(.+(\+|%|\.format\(|f[\"'])",
            r"\braw\(.+(\+|%|\.format\(|f[\"'])",
        ),
        explanation=(
            "User-controlled data appears to be concatenated into a SQL query. "
            "An attacker could alter the query and read, modify, or delete data."
        ),
        fix=(
            "Use parameterized queries or an ORM query builder. Never build SQL by "
            "joining strings with request data."
        ),
        secure_example='cursor.execute("SELECT * FROM users WHERE id = ?", [user_id])',
        learning=(
            "Real impact: attackers can bypass login forms, dump tables, or destroy "
            "records when SQL treats input as executable syntax."
        ),
    ),
    Rule(
        type="Command Injection",
        severity="Critical",
        cwe="CWE-78",
        owasp="A03:2021 Injection",
        patterns=_compile(
            r"\b(os\.system|popen|commands\.getoutput)\(",
            r"\bsubprocess\.(run|call|Popen|check_output)\(.+shell\s*=\s*True",
            r"\bexec\(.+request",
        ),
        explanation=(
            "The code appears to execute operating-system commands with dynamic input. "
            "If attacker input reaches this call, it can run arbitrary commands."
        ),
        fix=(
            "Avoid shell execution. Pass command arguments as a list, validate allowed "
            "values, and keep user input out of the shell."
        ),
        secure_example='subprocess.run(["git", "status"], check=True, shell=False)',
        learning=(
            "Real impact: command injection can become full server takeover because "
            "the application starts acting as a terminal for the attacker."
        ),
    ),
    Rule(
        type="Cross-Site Scripting",
        severity="High",
        cwe="CWE-79",
        owasp="A03:2021 Injection",
        patterns=_compile(
            r"\.innerHTML\s*=",
            r"dangerouslySetInnerHTML",
            r"\bdocument\.write\(",
            r"\bv-html\b",
        ),
        explanation=(
            "HTML is being written directly into the page. If the value contains "
            "untrusted data, an attacker can inject scripts into another user's browser."
        ),
        fix=(
            "Render untrusted values as text, sanitize trusted rich HTML with a proven "
            "library, and keep framework escaping enabled."
        ),
        secure_example="element.textContent = userControlledValue;",
        learning=(
            "Real impact: XSS can steal sessions, perform actions as the victim, or "
            "modify what users see inside the app."
        ),
    ),
    Rule(
        type="Hardcoded Secret",
        severity="High",
        cwe="CWE-798",
        owasp="A07:2021 Identification and Authentication Failures",
        patterns=_compile(
            r"(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"']{8,}[\"']",
            r"AKIA[0-9A-Z]{16}",
            r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        ),
        explanation=(
            "A credential-like value appears to be committed in source code. Secrets "
            "in code are easy to leak through Git history, logs, or screenshots."
        ),
        fix=(
            "Move secrets into environment variables or a secret manager. Rotate any "
            "credential that has already been committed."
        ),
        secure_example='api_key = os.environ["AUTOSECAI_API_KEY"]',
        learning=(
            "Real impact: leaked secrets often give direct access to databases, cloud "
            "accounts, CI systems, or third-party APIs."
        ),
    ),
    Rule(
        type="Insecure Deserialization",
        severity="Critical",
        cwe="CWE-502",
        owasp="A08:2021 Software and Data Integrity Failures",
        patterns=_compile(
            r"\bpickle\.loads?\(",
            r"\byaml\.load\(.+(Loader\s*=\s*yaml\.Loader|FullLoader)",
            r"\bmarshal\.loads?\(",
        ),
        explanation=(
            "The code appears to deserialize complex objects from data. Some formats "
            "can execute code during loading when the input is attacker-controlled."
        ),
        fix=(
            "Use safe data formats such as JSON, or safe loaders such as "
            "yaml.safe_load. Never unpickle untrusted input."
        ),
        secure_example="data = json.loads(request.body)",
        learning=(
            "Real impact: unsafe deserialization can execute attacker code before your "
            "business logic sees the value."
        ),
    ),
    Rule(
        type="Weak Password Hashing",
        severity="High",
        cwe="CWE-327",
        owasp="A02:2021 Cryptographic Failures",
        patterns=_compile(
            r"hashlib\.(md5|sha1)\(",
            r"crypto\.createHash\(['\"](md5|sha1)['\"]\)",
            r"MessageDigest\.getInstance\(['\"](MD5|SHA-1)['\"]\)",
        ),
        explanation=(
            "MD5 and SHA-1 are too fast and collision-prone for password storage or "
            "security-sensitive integrity checks."
        ),
        fix=(
            "For passwords, use bcrypt, Argon2, scrypt, or the framework password "
            "hasher. For integrity, use SHA-256 or better with HMAC when keyed."
        ),
        secure_example="hashed = make_password(password)",
        learning=(
            "Real impact: fast hashes help attackers crack stolen password databases "
            "at massive speed."
        ),
    ),
    Rule(
        type="Weak Randomness",
        severity="Medium",
        cwe="CWE-338",
        owasp="A02:2021 Cryptographic Failures",
        patterns=_compile(
            r"\brandom\.(random|randint|choice|choices|shuffle)\(",
            r"\bMath\.random\(",
            r"\bnew Random\(",
        ),
        explanation=(
            "General-purpose random number generators are predictable and should not "
            "create tokens, reset links, API keys, or session identifiers."
        ),
        fix=(
            "Use a cryptographically secure generator such as Python `secrets`, "
            "browser `crypto.getRandomValues`, or Node `crypto.randomBytes`."
        ),
        secure_example="token = secrets.token_urlsafe(32)",
        learning=(
            "Real impact: predictable tokens let attackers guess password reset links "
            "or impersonate users."
        ),
    ),
    Rule(
        type="Path Traversal",
        severity="High",
        cwe="CWE-22",
        owasp="A01:2021 Broken Access Control",
        patterns=_compile(
            r"\bopen\(.+request\.",
            r"\b(open|readFile|send_file|FileResponse)\(.+(\+|%|\.format\(|f[\"'])",
            r"\.\./",
        ),
        explanation=(
            "The code may build file paths from untrusted input. Attackers can use "
            "`../` segments to read files outside the intended directory."
        ),
        fix=(
            "Resolve paths against an allowlisted base directory, normalize them, and "
            "reject paths that escape the base."
        ),
        secure_example="safe_path = (BASE_DIR / filename).resolve(); assert safe_path.is_relative_to(BASE_DIR)",
        learning=(
            "Real impact: path traversal can expose source code, configuration, "
            "private keys, or user-uploaded files."
        ),
    ),
    Rule(
        type="Server-Side Request Forgery",
        severity="High",
        cwe="CWE-918",
        owasp="A10:2021 Server-Side Request Forgery",
        patterns=_compile(
            r"\brequests\.(get|post|put|delete)\(.+request\.",
            r"\bfetch\(.+(req\.|request\.)",
            r"\baxios\.(get|post|put|delete)\(.+(req\.|request\.)",
        ),
        explanation=(
            "The server appears to request a URL influenced by user input. Attackers "
            "can abuse this to reach internal services or cloud metadata endpoints."
        ),
        fix=(
            "Allowlist destination hosts, block private network ranges, enforce HTTPS, "
            "and use short timeouts."
        ),
        secure_example='assert parsed.hostname in {"api.partner.example"}',
        learning=(
            "Real impact: SSRF can expose admin panels, metadata credentials, or "
            "internal APIs that were never meant to face the internet."
        ),
    ),
    Rule(
        type="Debug Mode Enabled",
        severity="Medium",
        cwe="CWE-489",
        owasp="A05:2021 Security Misconfiguration",
        patterns=_compile(
            r"\bDEBUG\s*=\s*True\b",
            r"\bdebug\s*:\s*true\b",
            r"\bapp\.run\(.+debug\s*=\s*True",
        ),
        explanation=(
            "Debug mode exposes detailed errors and sometimes interactive consoles. "
            "It should never be enabled in production."
        ),
        fix=(
            "Read debug flags from environment-specific configuration and default to "
            "False for deployed environments."
        ),
        secure_example='DEBUG = os.getenv("APP_ENV") == "development"',
        learning=(
            "Real impact: verbose stack traces reveal paths, dependency versions, "
            "environment data, and implementation details attackers use for chaining."
        ),
    ),
    Rule(
        type="Disabled TLS Verification",
        severity="High",
        cwe="CWE-295",
        owasp="A02:2021 Cryptographic Failures",
        patterns=_compile(
            r"verify\s*=\s*False",
            r"rejectUnauthorized\s*:\s*false",
            r"NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*[\"']0[\"']",
        ),
        explanation=(
            "TLS certificate verification appears to be disabled. This allows "
            "man-in-the-middle attacks against outbound connections."
        ),
        fix=(
            "Keep certificate verification enabled. If needed, configure a trusted CA "
            "bundle instead of disabling validation."
        ),
        secure_example="requests.get(url, timeout=5)",
        learning=(
            "Real impact: attackers on the network can impersonate services and read "
            "or modify traffic."
        ),
    ),
)


def scan_source(code: str, language: str = "auto", learning_mode: bool = True) -> dict:
    started = perf_counter()
    normalized_code = code.replace("\r\n", "\n")
    lines = normalized_code.split("\n")

    issues = []
    seen: set[tuple[str, int, str]] = set()

    for line_number, line in enumerate(lines, start=1):
        for rule in RULES:
            if _matches(rule, line):
                fingerprint = _fingerprint(rule.type, line_number, line)
                dedupe_key = (rule.type, line_number, line.strip())
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                issues.append(_issue_payload(rule, line, line_number, fingerprint, learning_mode))

    issues.sort(key=lambda issue: (-SEVERITY_WEIGHT[issue["severity"]], issue["line"], issue["type"]))

    summary = _summary(issues, lines, language, perf_counter() - started)
    return {
        "issues": issues,
        "summary": summary,
        "engine": {
            "name": "AutoSecAI Heuristic Scanner",
            "mode": "learning" if learning_mode else "standard",
            "rules_loaded": len(RULES),
        },
    }


def _matches(rule: Rule, line: str) -> bool:
    return any(pattern.search(line) for pattern in rule.patterns)


def _issue_payload(
    rule: Rule,
    line: str,
    line_number: int,
    fingerprint: str,
    learning_mode: bool,
) -> dict:
    payload = {
        "id": fingerprint,
        "type": rule.type,
        "severity": rule.severity,
        "cwe": rule.cwe,
        "owasp": rule.owasp,
        "line": line_number,
        "vulnerable_snippet": line.strip(),
        "explanation": rule.explanation,
        "fix": rule.fix,
        "secure_example": rule.secure_example,
        "confidence": "Pattern Match",
    }
    if learning_mode:
        payload["learning"] = rule.learning
    return payload


def _summary(issues: list[dict], lines: Iterable[str], language: str, elapsed: float) -> dict:
    severity_counts = {severity: 0 for severity in SEVERITY_WEIGHT}
    for issue in issues:
        severity_counts[issue["severity"]] += 1

    risk_score = min(
        100,
        sum(SEVERITY_WEIGHT[issue["severity"]] for issue in issues),
    )

    return {
        "issue_count": len(issues),
        "risk_score": risk_score,
        "severity_counts": severity_counts,
        "language": language,
        "lines_scanned": len(list(lines)),
        "scan_time_ms": round(elapsed * 1000, 2),
    }


def _fingerprint(issue_type: str, line_number: int, line: str) -> str:
    digest = hashlib.sha1(f"{issue_type}:{line_number}:{line.strip()}".encode("utf-8")).hexdigest()
    return f"ASEC-{digest[:10].upper()}"

