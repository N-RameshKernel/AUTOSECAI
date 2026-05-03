# AutoSecAI // HYPER 3D MODE

> **AI-powered vulnerability detection and automated code-fix recommendation web application.**  
> Combines a futuristic 3D cyber interface with a backend security scanning engine that detects common source-code vulnerabilities, explains them in human-readable language, and recommends secure fixes.

---

## Project Idea

AutoSecAI is designed to make secure coding easier for developers and beginners. Traditional tools such as CodeQL and SonarQube can detect issues, but their explanations are often difficult for new developers to understand. AutoSecAI bridges that gap by combining static code analysis concepts with AI-style explanation and remediation guidance.

The system scans source code for known vulnerability patterns inspired by the OWASP Top 10, identifies risky code, explains the real-world impact, and suggests safer implementation patterns.

---

## Key Features

### 3D Interface
- Cyberpunk 3D web interface built with Three.js
- Infinite-depth floating panel environment
- Mouse-based camera rotation
- Smooth scrolling and velocity-based motion effects
- RGB glitch distortion during high-speed movement

### Security Engine
- Vulnerability scan REST API
- Human-readable security explanations
- Secure code-fix recommendations
- Learning mode for beginners
- Severity-colored vulnerability result cards

### Developer Experience
- Monaco-style code editor with fallback textarea support
- Real-time HUD displaying FPS, velocity, camera data, and issue count

---

## Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| HTML5 / CSS3 | Structure & styling |
| Vanilla JavaScript | Core logic |
| Three.js | 3D rendering engine |
| Monaco Editor | Code input with syntax highlighting |
| Lenis Smooth Scroll | Velocity-based smooth scrolling |

### Backend
| Technology | Purpose |
|---|---|
| Python | Core language |
| Django REST | API framework |
| SQLite | Local development database |
| PostgreSQL | Production-ready configuration |

---

## Vulnerabilities Detected

AutoSecAI currently detects patterns for the following vulnerability classes, inspired by the OWASP Top 10:

| Vulnerability | Severity |
|---|---|
| SQL Injection | 🔴 High |
| Command Injection | 🔴 High |
| Insecure Deserialization | 🔴 High |
| Path Traversal | 🔴 High |
| Cross-Site Scripting (XSS) | 🟡 Medium |
| Hardcoded Secrets | 🟡 Medium |
| Weak Password Hashing | 🟡 Medium |
| Weak Randomness | 🟡 Medium |
| Server-Side Request Forgery (SSRF) | 🟡 Medium |
| Debug Mode Enabled | 🔵 Low |
| Disabled TLS Verification | 🔵 Low |

---

## How to Run

### Quick Start (Dev Server)

```bash
cd "/mnt/c/Users/galax/Downloads/New folder/autosecai_hyper3d"
python3 dev_server.py
```

Then open: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### Django Option (Full Setup)

```bash
cd autosecai_hyper3d

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

---

## API Reference

### `POST /api/scan/`

Scan source code for vulnerabilities.

**Request Body**

```json
{
  "code": "query = \"SELECT * FROM users WHERE id=\" + user_id",
  "language": "python",
  "learning_mode": true
}
```

| Field | Type | Description |
|---|---|---|
| `code` | `string` | The source code to scan |
| `language` | `string` | Programming language (e.g. `"python"`, `"javascript"`) |
| `learning_mode` | `boolean` | Enable beginner-friendly explanations |

**Response**

```json
{
  "issues": [
    {
      "type": "SQL Injection",
      "severity": "High",
      "explanation": "User-controlled data appears to be concatenated into a SQL query.",
      "fix": "Use parameterized queries or an ORM query builder."
    }
  ]
}
```

---

## Sample Input — Vulnerable Code

The following Python snippet triggers **7+ vulnerability detections** across multiple categories:

```python
import pickle
import random
import hashlib
import subprocess
from flask import request

DEBUG = True                                       # ⚠ Debug Mode Enabled
API_SECRET = "super-secret-admin-token"            # ⚠ Hardcoded Secret

def find_user(db, user_id):
    query = "SELECT * FROM users WHERE id = " + user_id  # ⚠ SQL Injection
    return db.execute(query)

def run_ping(host):
    subprocess.run("ping -c 1 " + host, shell=True)      # ⚠ Command Injection

def load_profile():
    return pickle.loads(request.data)                     # ⚠ Insecure Deserialization

def reset_token():
    return str(random.randint(100000, 999999))            # ⚠ Weak Randomness

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()     # ⚠ Weak Password Hashing

def render_name(element, name):
    element.innerHTML = name                              # ⚠ Cross-Site Scripting
```

---

## Project Goal

The goal of AutoSecAI is to create an immersive developer security tool that combines:

- **3D Graphics** — an unforgettable, gamified interface that makes security feel engaging
- **AI-Style Explanation** — plain-language reasoning any developer can understand
- **Static Code Analysis** — pattern-based detection grounded in OWASP standards
- **Secure Coding Education** — a learning mode that teaches developers *why* code is vulnerable
- **Automated Remediation Guidance** — actionable fixes, not just warnings

> AutoSecAI is not just a dashboard. It is designed to feel like an **AI-powered cyber operating system** for secure development.

---

## License

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright 2024 AutoSecAI

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

### What this means

| Permission | Condition | Limitation |
|---|---|---|
| ✅ Commercial use | Include license & copyright notice | ❌ Liability |
| ✅ Modification | State changes made | ❌ Warranty |
| ✅ Distribution | Include full Apache 2.0 text | |
| ✅ Patent use | | |
| ✅ Private use | | |

See the full license text at [apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0).
