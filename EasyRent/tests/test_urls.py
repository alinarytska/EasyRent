from django.test import SimpleTestCase
from django.urls import reverse


class ProjectURLTests(SimpleTestCase):
    def test_root_redirects_to_api_docs(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/api/v1/docs/")

    def test_api_v1_root_redirects_to_api_docs(self):
        response = self.client.get("/api/v1/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "docs/")

    def test_api_docs_url_is_resolvable(self):
        self.assertEqual(reverse("swagger-ui"), "/api/v1/docs/")
