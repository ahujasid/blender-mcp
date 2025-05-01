"""
Tests for the OpenAI adapter class.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from blender_mcp_openai.adapter import OpenAIAdapter
from blender_mcp_openai.config import OpenAIConfig


class TestOpenAIAdapter(unittest.TestCase):
    """Tests for the OpenAIAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock MCP server module
        self.mock_mcp_server = MagicMock()
        self.mock_mcp_server.mcp = MagicMock()
        self.mock_mcp_server.mcp.tools = {
            "test_tool": self._create_mock_tool()
        }
        
        # Create a mock OpenAI client
        self.mock_openai_client = MagicMock()
        
        # Create a configuration
        self.config = OpenAIConfig(
            model="gpt-4-test",
            api_key="test_api_key",
            temperature=0.5
        )
    
    def _create_mock_tool(self):
        """Create a mock tool function for testing."""
        def mock_tool(ctx, name: str, count: int = 1):
            """
            A mock tool for testing.
            
            Args:
                ctx: The context object
                name: A name parameter
                count: A count parameter
            """
            return f"Tool executed with name={name}, count={count}"
        
        return mock_tool
    
    @patch('blender_mcp_openai.adapter.OpenAI')
    def test_initialization(self, mock_openai_class):
        """Test adapter initialization."""
        # Configure the mock
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        
        # Create the adapter
        adapter = OpenAIAdapter(
            config=self.config,
            mcp_server=self.mock_mcp_server
        )
        
        # Verify the initialization
        mock_openai_class.assert_called_once_with(api_key="test_api_key")
        self.assertEqual(adapter.config.openai.model, "gpt-4-test")
        self.assertEqual(adapter.config.openai.temperature, 0.5)
        self.assertEqual(len(adapter.tools), 1)
        
        # Check that the tool schema was extracted correctly
        tool_schema = adapter.tools[0]["function"]
        self.assertEqual(tool_schema["name"], "test_tool")
        self.assertIn("parameters", tool_schema)
        self.assertIn("name", tool_schema["parameters"]["properties"])
        self.assertIn("count", tool_schema["parameters"]["properties"])
    
    @patch('blender_mcp_openai.adapter.OpenAI')
    def test_sync_chat_without_tools(self, mock_openai_class):
        """Test synchronous chat without tool calls."""
        # Configure the mock
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        
        # Configure the completion response
        completion_response = MagicMock()
        completion_response.choices = [MagicMock()]
        completion_response.choices[0].message = MagicMock()
        completion_response.choices[0].message.content = "Test response"
        completion_response.choices[0].message.tool_calls = None
        
        mock_openai_instance.chat.completions.create.return_value = completion_response
        
        # Create the adapter
        adapter = OpenAIAdapter(
            config=self.config,
            mcp_server=self.mock_mcp_server
        )
        
        # Call the chat method
        response = adapter.chat([{"role": "user", "content": "Test message"}])
        
        # Verify the response
        self.assertEqual(response, "Test response")
        mock_openai_instance.chat.completions.create.assert_called_once()
        
        # Check that the parameters were passed correctly
        call_args = mock_openai_instance.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4-test")
        self.assertEqual(call_args["temperature"], 0.5)
        self.assertEqual(call_args["messages"], [{"role": "user", "content": "Test message"}])
        self.assertEqual(len(call_args["tools"]), 1)
        self.assertFalse(call_args["stream"])
    
    @patch('blender_mcp_openai.adapter.OpenAI')
    def test_streaming_chat(self, mock_openai_class):
        """Test streaming chat."""
        # Configure the mock
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        
        # Configure the streaming response
        mock_stream = MagicMock()
        mock_openai_instance.chat.completions.create.return_value = mock_stream
        
        # Create the adapter
        adapter = OpenAIAdapter(
            config=self.config,
            mcp_server=self.mock_mcp_server
        )
        
        # Call the chat method with streaming
        stream = adapter.chat([{"role": "user", "content": "Test message"}], stream=True)
        
        # Verify that a stream was returned
        self.assertTrue(hasattr(stream, '__iter__'))
        
        # Check that the parameters were passed correctly
        call_args = mock_openai_instance.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4-test")
        self.assertEqual(call_args["messages"], [{"role": "user", "content": "Test message"}])
        self.assertTrue(call_args["stream"])


if __name__ == "__main__":
    unittest.main() 