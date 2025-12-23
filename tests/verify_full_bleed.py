import unittest
from unittest.mock import patch, MagicMock
from bookbuilder.convert import convert_markdown_to_pdf
import os

class TestFullBleed(unittest.TestCase):
    @patch('bookbuilder.convert.HTML')
    @patch('bookbuilder.convert.markdown.markdown')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='# Cover\nContent')
    def test_full_bleed_css(self, mock_open, mock_markdown, mock_html):
        mock_markdown.return_value = '<h1>Cover</h1><p>Content</p>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        
        pdf_path = './test_cover.pdf'
        md_path = './test_cover.md'
        
        # Test with full_bleed=True
        convert_markdown_to_pdf(md_path, pdf_path, full_bleed=True)
        
        # Verify HTML was called with margin: 0 and content: none
        call_args = mock_html.call_args
        html_string = call_args[1]['string']
        
        self.assertIn('margin: 0;', html_string)
        self.assertIn('content: none;', html_string)
        
        # Test with full_bleed=False (default)
        convert_markdown_to_pdf(md_path, pdf_path, full_bleed=False)
        
        call_args = mock_html.call_args
        html_string = call_args[1]['string']
        
        self.assertNotIn('margin: 0;', html_string)
        # Default margins should be present (e.g., 1in)
        self.assertIn('margin: 1in 0.8in 1in 0.8in;', html_string)

if __name__ == '__main__':
    unittest.main()
