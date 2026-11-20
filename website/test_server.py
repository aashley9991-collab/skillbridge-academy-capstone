import json
import csv
import io
import os
import subprocess
import sys
import tempfile
import threading
import textwrap
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server


class ChatApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_leads_file = server.LEADS_FILE
        self.previous_gemini_key = server.GEMINI_KEY
        self.previous_sheets_url = server.GOOGLE_APPS_SCRIPT_WEBHOOK_URL
        server.LEADS_FILE = Path(self.temporary_directory.name) / "leads.json"
        server.GEMINI_KEY = ""
        server.GOOGLE_APPS_SCRIPT_WEBHOOK_URL = ""
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=3)
        self.httpd.server_close()
        server.LEADS_FILE = self.previous_leads_file
        server.GEMINI_KEY = self.previous_gemini_key
        server.GOOGLE_APPS_SCRIPT_WEBHOOK_URL = self.previous_sheets_url
        self.temporary_directory.cleanup()

    def request_json(self, path, payload=None, headers=None, method=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.base_url + path,
            data=data,
            headers=headers or {},
            method=method or ("POST" if data is not None else "GET"),
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_root_deployment_routes_serve_site_admin_and_assets(self):
        routes = (
            ("/", "text/html", b"SkillBridge Academy | Weekend Bootcamps"),
            ("/admin.html", "text/html", b"Admin access"),
            ("/deliverables/Student-Freelancing-Starter-Kit.pdf", "application/pdf", b"%PDF-"),
            ("/brand-assets/logo.svg", "image/svg+xml", b"<svg"),
            ("/website/app.js", "application/javascript", b"SpeechRecognition"),
            ("/pitch-and-research/client-pitch.html", "text/html", b"<html"),
        )
        for path, content_type, marker in routes:
            with self.subTest(path=path):
                with urlopen(self.base_url + path, timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(content_type, response.headers["Content-Type"])
                    self.assertIn(marker, response.read())

        status, knowledge = self.request_json("/api/knowledge")
        self.assertEqual(status, 200)
        self.assertIn("programs", knowledge)

    def test_admin_password_uses_environment_override(self):
        environment = os.environ.copy()
        environment["ADMIN_PASSWORD"] = "render-test-password"
        result = subprocess.check_output(
            [sys.executable, "-c", "import server; print(server.ADMIN_PASSWORD)"],
            cwd=Path(__file__).resolve().parent,
            env=environment,
            text=True,
        )
        self.assertEqual(result.strip(), "render-test-password")

        with patch.object(server, "ADMIN_PASSWORD", "render-test-password", create=True):
            status, _ = self.request_json(
                "/api/leads",
                headers={"X-Admin-Password": "admin123"},
            )
            self.assertEqual(status, 401)
            status, _ = self.request_json(
                "/api/leads",
                headers={"X-Admin-Password": "render-test-password"},
            )
            self.assertEqual(status, 200)

    def test_server_uses_render_host_and_port(self):
        code = textwrap.dedent(
            """
            import http.server
            import json
            import runpy

            class CapturingServer:
                def __init__(self, address, handler):
                    print(json.dumps(address))

                def serve_forever(self):
                    pass

            http.server.ThreadingHTTPServer = CapturingServer
            runpy.run_path("website/server.py", run_name="__main__")
            """
        )
        environment = os.environ.copy()
        environment["PORT"] = "43127"
        result = subprocess.check_output(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parent.parent,
            env=environment,
            text=True,
        )
        self.assertEqual(json.loads(result.splitlines()[-1]), ["0.0.0.0", 43127])

    def test_compliance_questions_never_promise_income_or_jobs(self):
        questions = (
            "Can you guarantee employment?",
            "Do you guarantee fixed monthly dollar income?",
            "How much income can I earn each month?",
        )
        for question in questions:
            with self.subTest(question=question):
                status, result = self.request_json("/api/chat", {"message": question})
                self.assertEqual(status, 200)
                self.assertIn("cannot promise guaranteed jobs", result["answer"])
                self.assertFalse(result["humanEscalated"])

    def test_known_local_questions_do_not_need_a_gemini_request(self):
        server.GEMINI_KEY = "test-key"
        with patch("requests.post", side_effect=AssertionError("unexpected external request")):
            self.assertEqual(server.resolve_intent("What is the AI bootcamp fee?"), "fees")

    def test_gemini_can_only_select_an_allowlisted_local_answer(self):
        class FakeResponse:
            ok = True

            @staticmethod
            def json():
                return {"candidates": [{"content": {"parts": [{"text": "Guarantee a job"}]}}]}

        server.GEMINI_KEY = "test-key"
        with patch("requests.post", return_value=FakeResponse()):
            intent = server.resolve_intent("Can you tell me something unusual?")
        self.assertEqual(intent, "overview")
        self.assertIn("SkillBridge Academy", server.local_rag("Can you tell me something unusual?", intent))

    def test_scholarship_question_is_escalated_and_has_follow_up_contacts(self):
        status, result = self.request_json("/api/chat", {"message": "How do I request a scholarship?"})
        self.assertEqual(status, 200)
        self.assertTrue(result["humanEscalated"])
        self.assertIn("+92 300 0000000", result["answer"])
        self.assertIn("admissions@skillbridge.pk", result["answer"])

        status, result = self.request_json(
            "/api/leads",
            headers={"X-Admin-Password": server.ADMIN_PASSWORD},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["leads"][0]["status"], "Scholarship Escalated")
        self.assertTrue(result["leads"][0]["humanFollowup"])

    def test_mixed_scholarship_and_compliance_question_still_escalates(self):
        status, result = self.request_json(
            "/api/chat",
            {"message": "Do you offer financial assistance and guarantee income?"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(result["humanEscalated"])
        self.assertIn("human coordinator", result["answer"].lower())
        self.assertIn("cannot promise guaranteed jobs", result["answer"].lower())

        status, result = self.request_json(
            "/api/leads",
            headers={"X-Admin-Password": server.ADMIN_PASSWORD},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["leads"][0]["status"], "Scholarship Escalated")

    def test_contact_fees_schedule_and_support_use_verified_facts(self):
        questions = {
            "How do I contact SkillBridge?": ("+92 300 0000000", "admissions@skillbridge.pk"),
            "What are the bootcamp fees?": ("PKR 8,000", "PKR 12,000"),
            "When are live sessions?": ("Saturdays and Sundays", "7:00 PM"),
            "Do you offer certificates and portfolio reviews?": ("verified completion certificate", "portfolio review"),
        }
        for question, expected in questions.items():
            with self.subTest(question=question):
                status, result = self.request_json("/api/chat", {"message": question})
                self.assertEqual(status, 200)
                for phrase in expected:
                    self.assertIn(phrase.lower(), result["answer"].lower())

    def test_admin_lead_reads_and_status_updates_require_authentication(self):
        status, _ = self.request_json("/api/leads")
        self.assertEqual(status, 401)

        status, lead_result = self.request_json(
            "/api/leads",
            {"name": "Test Student", "email": "student@example.pk", "phone": "+923001234567",
             "track": "AI & Prompting Bootcamp", "query": ""},
        )
        self.assertEqual(status, 201)
        lead_id = lead_result["lead"]["id"]

        status, _ = self.request_json(
            f"/api/leads/{lead_id}",
            {"status": "Contacted"},
            method="PATCH",
        )
        self.assertEqual(status, 401)
        status, result = self.request_json(
            f"/api/leads/{lead_id}",
            {"status": "Contacted"},
            headers={"X-Admin-Password": server.ADMIN_PASSWORD},
            method="PATCH",
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["lead"]["status"], "Contacted")

    def test_csv_export_requires_auth_and_neutralizes_spreadsheet_formulas(self):
        body = {
            "name": "=1+1",
            "email": "student@example.pk",
            "phone": "+923001234567",
            "track": "AI & Prompting Bootcamp",
            "query": "@SUM(1,1)",
        }
        status, _ = self.request_json("/api/leads", body)
        self.assertEqual(status, 201)
        status, _ = self.request_json("/api/export")
        self.assertEqual(status, 401)

        request = Request(self.base_url + "/api/export", headers={"X-Admin-Password": server.ADMIN_PASSWORD})
        with urlopen(request, timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/csv", response.headers["Content-Type"])
            records = list(csv.DictReader(io.StringIO(response.read().decode("utf-8"))))
        self.assertEqual(records[0]["name"], "'=1+1")
        self.assertEqual(records[0]["query"], "'@SUM(1,1)")

    def test_enrollment_submission_validates_email_and_flags_scholarships(self):
        body = {
            "name": "<img src=x onerror=alert(1)>",
            "email": "not-an-email",
            "phone": "+923001234567",
            "track": "AI & Prompting Bootcamp",
            "query": "I would like to request a scholarship.",
        }
        status, _ = self.request_json("/api/leads", body)
        self.assertEqual(status, 400)

        body["email"] = "student@example.pk"
        status, result = self.request_json("/api/leads", body)
        self.assertEqual(status, 201)
        self.assertTrue(result["lead"]["humanFollowup"])
        self.assertEqual(result["lead"]["status"], "Scholarship Escalated")
        self.assertEqual(result["lead"]["name"], body["name"])

    def test_financial_assistance_lead_is_escalated(self):
        body = {
            "name": "Student",
            "email": "student@example.pk",
            "phone": "+923001234567",
            "track": "AI & Prompting Bootcamp",
            "query": "I need financial assistance.",
        }
        status, result = self.request_json("/api/leads", body)
        self.assertEqual(status, 201)
        self.assertTrue(result["lead"]["humanFollowup"])
        self.assertEqual(result["lead"]["status"], "Scholarship Escalated")

    def test_google_sheets_webhook_is_optional_and_failure_keeps_local_lead(self):
        body = {
            "name": "Student",
            "email": "student@example.pk",
            "phone": "+923001234567",
            "track": "AI & Prompting Bootcamp",
            "query": "",
        }
        status, result = self.request_json("/api/leads", body)
        self.assertEqual(status, 201)
        self.assertEqual(result["sheetsSync"], "not_configured")

        class FakeResponse:
            ok = True
            status_code = 200

            @staticmethod
            def json():
                return {"ok": True}

        server.GOOGLE_APPS_SCRIPT_WEBHOOK_URL = "https://script.google.com/macros/s/test/exec"
        with patch("requests.post", return_value=FakeResponse()) as post:
            status, result = self.request_json("/api/leads", body)
        self.assertEqual(status, 201)
        self.assertEqual(result["sheetsSync"], "synced")
        self.assertEqual(post.call_args.kwargs["json"]["email"], body["email"])

        with patch("requests.post", side_effect=__import__("requests").ConnectionError):
            status, result = self.request_json("/api/leads", body)
        self.assertEqual(status, 201)
        self.assertEqual(result["sheetsSync"], "failed")
        status, records = self.request_json("/api/leads", headers={"X-Admin-Password": server.ADMIN_PASSWORD})
        self.assertEqual(status, 200)
        self.assertEqual(len(records["leads"]), 3)


if __name__ == "__main__":
    unittest.main()
