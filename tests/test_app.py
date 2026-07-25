import os
import unittest

import app


class BuildAiResponseTest(unittest.TestCase):
    def test_falls_back_to_helpful_local_response_when_key_is_missing(self):
        os.environ.pop("OPENAI_API_KEY", None)
        response = app.build_ai_response("Suggest a study plan")
        self.assertTrue(response)
        self.assertNotIn("OpenAI API key", response)
        self.assertIn("study", response.lower())


if __name__ == "__main__":
    unittest.main()
