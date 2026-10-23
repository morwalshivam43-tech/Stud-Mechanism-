import unittest
import app as study_app

class AppSmokeTests(unittest.TestCase):
    def setUp(self):
        study_app.app.config["TESTING"] = True
        self.client = study_app.app.test_client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"StudyMate", response.data)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_stats_api(self):
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        self.assertIn("documents", response.get_json())

if __name__ == "__main__":
    unittest.main()
