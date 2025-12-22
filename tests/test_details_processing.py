"""
Unit tests for details tag processing functionality.

Tests cover:
- Basic details tag transformation
- Nested HTML content handling
- Multiple details blocks in same file
- Config toggle behavior (enabled/disabled)
- Format-specific behavior (pdf vs epub)
"""

import pytest
from bookbuilder.utils import process_details_tags


class TestProcessDetailsTags:
    """Tests for process_details_tags function."""
    
    def test_basic_transformation_pdf(self):
        """Transform details tag to static content for PDF."""
        content = '''<details>
<summary><strong>Click to Reveal Answers</strong></summary>

1. **Answer one**
2. **Answer two**
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf', 'docx'],
            'staticReplacement': {
                'showSummary': True,
                'summaryPrefix': '',
                'addHorizontalRule': True
            }
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        # Should have horizontal rule
        assert '---' in result
        # Should have the summary text
        assert 'Click to Reveal Answers' in result
        # Should have the content
        assert '**Answer one**' in result
        assert '**Answer two**' in result
        # Should NOT have details tags
        assert '<details>' not in result
        assert '</details>' not in result
        assert '<summary>' not in result
    
    def test_preserve_for_epub(self):
        """Details tags should remain intact for EPUB format."""
        content = '''<details>
<summary><strong>Click to Reveal</strong></summary>
Content here
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf', 'docx'],
            'interactiveFormats': ['epub', 'html']
        }
        
        result = process_details_tags(content, 'epub', settings)
        
        # Should remain unchanged
        assert result == content
    
    def test_preserve_for_html(self):
        """Details tags should remain intact for HTML format."""
        content = '''<details>
<summary>Click here</summary>
Hidden content
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf', 'docx']
        }
        
        result = process_details_tags(content, 'html', settings)
        
        # Should remain unchanged
        assert result == content
    
    def test_disabled_setting(self):
        """When disabled, content should remain unchanged for all formats."""
        content = '''<details>
<summary>Click</summary>
Content
</details>'''
        
        settings = {
            'enabled': False,
            'staticFormats': ['pdf', 'docx']
        }
        
        # Even for PDF, should remain unchanged when disabled
        result = process_details_tags(content, 'pdf', settings)
        assert '<details>' in result
    
    def test_multiple_details_blocks(self):
        """Handle multiple details blocks in same content."""
        content = '''# Quiz Section

<details>
<summary>Question 1 Answer</summary>
The answer is A.
</details>

Some text in between.

<details>
<summary>Question 2 Answer</summary>
The answer is B.
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf'],
            'staticReplacement': {
                'showSummary': True,
                'addHorizontalRule': True
            }
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        # Both should be transformed
        assert '<details>' not in result
        assert 'Question 1 Answer' in result
        assert 'Question 2 Answer' in result
        assert 'The answer is A.' in result
        assert 'The answer is B.' in result
        # Original text preserved
        assert 'Some text in between.' in result
    
    def test_summary_prefix(self):
        """Summary prefix should be applied."""
        content = '''<details>
<summary>Answers</summary>
Content
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf'],
            'staticReplacement': {
                'showSummary': True,
                'summaryPrefix': '📋 ',
                'addHorizontalRule': False
            }
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        assert '📋 **Answers**' in result
    
    def test_no_horizontal_rule(self):
        """Horizontal rule should be optional."""
        content = '''<details>
<summary>Answer</summary>
Content
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf'],
            'staticReplacement': {
                'showSummary': True,
                'addHorizontalRule': False
            }
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        # No intro horizontal rule (there shouldn't be just '---' after the content)
        # Note: we're checking that we don't add HR, but the content might have other dashes
        lines = result.strip().split('\n')
        # First non-empty line should NOT be just '---'
        first_non_empty = next((l for l in lines if l.strip()), '')
        assert first_non_empty.strip() != '---'
    
    def test_no_summary_display(self):
        """Summary can be hidden."""
        content = '''<details>
<summary>Click to show</summary>
The actual content
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf'],
            'staticReplacement': {
                'showSummary': False,
                'addHorizontalRule': True
            }
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        # Content should be present
        assert 'The actual content' in result
        # Summary text should not be in output (as a heading)
        assert '**Click to show**' not in result
    
    def test_empty_settings(self):
        """Default behavior with minimal settings."""
        content = '''<details>
<summary>Summary</summary>
Content
</details>'''
        
        # With no explicit settings, defaults should work
        result = process_details_tags(content, 'pdf', {})
        
        # Should be transformed since 'pdf' is in default staticFormats
        assert '<details>' not in result
    
    def test_none_settings(self):
        """Handle None settings gracefully."""
        content = '''<details>
<summary>Summary</summary>
Content
</details>'''
        
        result = process_details_tags(content, 'pdf', None)
        
        # Should still transform
        assert '<details>' not in result
    
    def test_strip_html_from_summary(self):
        """HTML tags in summary should be stripped."""
        content = '''<details>
<summary><strong>Bold</strong> and <em>italic</em> text</summary>
Content
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf'],
            'staticReplacement': {'showSummary': True}
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        # HTML tags should be stripped, text preserved
        assert '**Bold and italic text**' in result
        assert '<strong>' not in result
        assert '<em>' not in result
    
    def test_case_insensitive_tags(self):
        """Handle case variations in HTML tags."""
        content = '''<DETAILS>
<SUMMARY>Answer</SUMMARY>
Content here
</DETAILS>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf']
        }
        
        result = process_details_tags(content, 'pdf', settings)
        
        assert '<DETAILS>' not in result
        assert 'Answer' in result
        assert 'Content here' in result
    
    def test_docx_format(self):
        """DOCX should also be treated as static format by default."""
        content = '''<details>
<summary>Answer</summary>
Content
</details>'''
        
        settings = {
            'enabled': True,
            'staticFormats': ['pdf', 'docx']
        }
        
        result = process_details_tags(content, 'docx', settings)
        
        assert '<details>' not in result
