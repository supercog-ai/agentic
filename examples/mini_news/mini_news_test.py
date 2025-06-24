import unittest
import os
from datetime import datetime
from unittest.mock import patch, mock_open
from mini_news import MiniNewsAgent


class TestMiniNewsAgent(unittest.TestCase):
    def setUp(self):
        self.agent = MiniNewsAgent()
        self.test_html = "<div class='news-item'><h3>Test News</h3></div>"
        
    def test_write_file_creates_file(self):
        # Set up test data
        current_date = "2025-06-22"
        html_filename = f"mini_news_{current_date}.html"
        
        # Get the expected path
        mini_news_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(mini_news_dir, html_filename)
        
        # Call the function
        self.agent.write_file(self.test_html, current_date)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(full_path))
        
        # Read the file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify the content
        self.assertIn("<style>", content)
        self.assertIn(self.test_html, content)
        
        # Clean up
        os.remove(full_path)

if __name__ == '__main__':
    unittest.main()
