import unittest

from scanner.engine import scan_source


class ScannerEngineTests(unittest.TestCase):
    def test_detects_sql_injection(self):
        result = scan_source('query = "SELECT * FROM users WHERE id=" + user_id')

        self.assertEqual(result["summary"]["issue_count"], 1)
        self.assertEqual(result["issues"][0]["type"], "SQL Injection")
        self.assertEqual(result["issues"][0]["severity"], "High")

    def test_detects_multiple_critical_issues(self):
        code = """
import pickle
import subprocess

payload = pickle.loads(request.body)
subprocess.run("ping " + host, shell=True)
"""
        result = scan_source(code)
        issue_types = {issue["type"] for issue in result["issues"]}

        self.assertIn("Insecure Deserialization", issue_types)
        self.assertIn("Command Injection", issue_types)
        self.assertGreaterEqual(result["summary"]["risk_score"], 90)

    def test_clean_code_has_zero_issues(self):
        code = """
def add(a, b):
    return a + b
"""
        result = scan_source(code)

        self.assertEqual(result["issues"], [])
        self.assertEqual(result["summary"]["risk_score"], 0)


if __name__ == "__main__":
    unittest.main()

