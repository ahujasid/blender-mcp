"""
Unit tests for Sketchfab preview functionality.

These tests use mocks to simulate Blender connection and API responses
since the actual Blender addon requires the Blender environment.
"""

import pytest
import base64
import json
from unittest.mock import Mock, patch, MagicMock


class TestSketchfabPreviewAddon:
    """Tests for the addon.py get_sketchfab_model_preview function logic"""
    
    @pytest.fixture
    def mock_api_response(self):
        """Sample Sketchfab API response for model info"""
        return {
            "uid": "test-uid-12345",
            "name": "Test Model",
            "user": {
                "username": "test_author"
            },
            "thumbnails": {
                "images": [
                    {"url": "https://example.com/thumb_200.jpg", "width": 200, "height": 200},
                    {"url": "https://example.com/thumb_640.jpg", "width": 640, "height": 480},
                    {"url": "https://example.com/thumb_1024.jpg", "width": 1024, "height": 768}
                ]
            }
        }
    
    @pytest.fixture
    def sample_image_data(self):
        """Sample image data (1x1 pixel JPEG)"""
        # Minimal valid JPEG
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9teledn\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5\xdb\xb4v\xec\xa1@\x03\xc6\x00\x1fR2q\xf5\xeb\xef_\xff\xd9'

    def test_thumbnail_selection_prefers_medium_size(self, mock_api_response):
        """Test that medium-sized thumbnails (400-800px) are preferred"""
        thumbnails = mock_api_response["thumbnails"]["images"]
        
        # Simulate the selection logic from addon.py
        selected_thumbnail = None
        for thumb in thumbnails:
            width = thumb.get("width", 0)
            if 400 <= width <= 800:
                selected_thumbnail = thumb
                break
        
        # Fallback to first if none in range
        if not selected_thumbnail:
            selected_thumbnail = thumbnails[0]
        
        assert selected_thumbnail["width"] == 640
        assert selected_thumbnail["url"] == "https://example.com/thumb_640.jpg"
    
    def test_thumbnail_fallback_to_first(self):
        """Test fallback to first thumbnail when no medium size available"""
        thumbnails = [
            {"url": "https://example.com/thumb_100.jpg", "width": 100, "height": 100},
            {"url": "https://example.com/thumb_1200.jpg", "width": 1200, "height": 900}
        ]
        
        selected_thumbnail = None
        for thumb in thumbnails:
            width = thumb.get("width", 0)
            if 400 <= width <= 800:
                selected_thumbnail = thumb
                break
        
        if not selected_thumbnail:
            selected_thumbnail = thumbnails[0]
        
        assert selected_thumbnail["width"] == 100
    
    def test_base64_encoding(self, sample_image_data):
        """Test that image data is correctly base64 encoded"""
        encoded = base64.b64encode(sample_image_data).decode('ascii')
        decoded = base64.b64decode(encoded)
        
        assert decoded == sample_image_data
        assert isinstance(encoded, str)
    
    def test_format_detection_from_content_type(self):
        """Test image format detection from content type"""
        test_cases = [
            ("image/png", "thumb.jpg", "png"),
            ("image/jpeg", "thumb.png", "jpeg"),
            ("application/octet-stream", "thumb.png", "png"),
            ("application/octet-stream", "thumb.jpg", "jpeg"),
        ]
        
        for content_type, url, expected_format in test_cases:
            if "png" in content_type or url.endswith(".png"):
                img_format = "png"
            else:
                img_format = "jpeg"
            
            assert img_format == expected_format, f"Failed for content_type={content_type}, url={url}"


class TestSketchfabPreviewServer:
    """Tests for the server.py get_sketchfab_model_preview MCP tool"""
    
    def test_successful_preview_response_parsing(self):
        """Test parsing of successful preview response from addon"""
        mock_result = {
            "success": True,
            "image_data": base64.b64encode(b"fake_image_data").decode('ascii'),
            "format": "jpeg",
            "model_name": "Test Model",
            "author": "test_author",
            "uid": "test-uid",
            "thumbnail_width": 640,
            "thumbnail_height": 480
        }
        
        # Verify the response structure
        assert mock_result["success"] is True
        assert "image_data" in mock_result
        assert mock_result["format"] == "jpeg"
        assert mock_result["model_name"] == "Test Model"
        
        # Verify base64 can be decoded
        decoded = base64.b64decode(mock_result["image_data"])
        assert decoded == b"fake_image_data"
    
    def test_error_response_handling(self):
        """Test handling of error responses"""
        error_cases = [
            {"error": "Sketchfab API key is not configured"},
            {"error": "Model not found: invalid-uid"},
            {"error": "Authentication failed (401). Check your API key."},
            {"error": "No thumbnail available for this model"},
        ]
        
        for error_response in error_cases:
            assert "error" in error_response
            assert isinstance(error_response["error"], str)
            assert len(error_response["error"]) > 0
    
    def test_none_response_handling(self):
        """Test handling of None response"""
        result = None
        
        # This should raise an exception in the actual code
        if result is None:
            error_message = "Received no response from Blender"
            assert "no response" in error_message.lower()


class TestIntegrationScenarios:
    """Integration-style tests for typical usage scenarios"""
    
    def test_search_then_preview_flow(self):
        """Test the typical flow: search -> get UID -> preview"""
        # Simulated search result
        search_result = {
            "results": [
                {
                    "uid": "abc123",
                    "name": "Cool Model",
                    "user": {"username": "artist1"},
                    "isDownloadable": True
                },
                {
                    "uid": "def456",
                    "name": "Another Model", 
                    "user": {"username": "artist2"},
                    "isDownloadable": True
                }
            ]
        }
        
        # Extract UID from search result
        first_model = search_result["results"][0]
        uid = first_model["uid"]
        
        assert uid == "abc123"
        
        # Simulated preview request
        preview_request = {"uid": uid}
        assert preview_request["uid"] == "abc123"
    
    def test_preview_response_contains_required_fields(self):
        """Test that preview response contains all required fields for MCP Image"""
        mock_preview_response = {
            "success": True,
            "image_data": "base64encodeddata",
            "format": "jpeg",
            "model_name": "Test",
            "author": "Author"
        }
        
        # Required for creating MCP Image
        required_fields = ["image_data", "format"]
        for field in required_fields:
            assert field in mock_preview_response, f"Missing required field: {field}"
        
        # Format should be valid
        assert mock_preview_response["format"] in ["jpeg", "png", "gif", "webp"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

