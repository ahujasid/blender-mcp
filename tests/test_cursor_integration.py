"""
Tests for Cursor integration features
"""

import unittest
import json
import os
import sys
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from blender_mcp.cursor_integration import CursorIntegration, CursorProjectInfo
    CURSOR_INTEGRATION_AVAILABLE = True
except ImportError:
    CURSOR_INTEGRATION_AVAILABLE = False


class TestCursorIntegration(unittest.TestCase):
    """Test cases for Cursor integration features"""
    
    def setUp(self):
        """Set up test environment"""
        if not CURSOR_INTEGRATION_AVAILABLE:
            self.skipTest("Cursor integration not available")
        
        self.cursor_integration = CursorIntegration()
    
    def test_project_info_detection(self):
        """Test that project information is detected correctly"""
        project_info = self.cursor_integration.project_info
        
        # Check that we have basic project info
        self.assertIsInstance(project_info, CursorProjectInfo)
        self.assertIsInstance(project_info.has_git, bool)
        self.assertIsInstance(project_info.python_version, str)
        self.assertIsInstance(project_info.has_requirements, bool)
        self.assertIsInstance(project_info.has_pyproject, bool)
    
    def test_project_context(self):
        """Test that project context is returned correctly"""
        context = self.cursor_integration.get_project_context()
        
        # Check that context is a dictionary with expected keys
        self.assertIsInstance(context, dict)
        self.assertIn("project_root", context)
        self.assertIn("has_git", context)
        self.assertIn("python_version", context)
        self.assertIn("has_requirements", context)
        self.assertIn("has_pyproject", context)
        self.assertIn("cursor_integration", context)
        self.assertTrue(context["cursor_integration"])
    
    def test_script_template_creation(self):
        """Test that script templates are created correctly"""
        script_name = "test_script"
        description = "Test script description"
        
        template = self.cursor_integration.create_blender_script_template(
            script_name, description
        )
        
        # Check that template contains expected elements
        self.assertIsInstance(template, str)
        self.assertIn(script_name, template)
        self.assertIn(description, template)
        self.assertIn("import bpy", template)
        self.assertIn("def main():", template)
    
    def test_config_template_creation(self):
        """Test that configuration templates are created correctly"""
        config = self.cursor_integration.create_cursor_config_template()
        
        # Check that config is valid JSON
        try:
            config_dict = json.loads(config)
        except json.JSONDecodeError:
            self.fail("Configuration template is not valid JSON")
        
        # Check that config has expected structure
        self.assertIn("mcpServers", config_dict)
        self.assertIn("blender", config_dict["mcpServers"])
        self.assertIn("command", config_dict["mcpServers"]["blender"])
        self.assertIn("args", config_dict["mcpServers"]["blender"])
    
    def test_workflow_script_creation(self):
        """Test that workflow scripts are created correctly"""
        workflow_name = "test_workflow"
        
        script = self.cursor_integration.create_development_workflow_script(
            workflow_name
        )
        
        # Check that script contains expected elements
        self.assertIsInstance(script, str)
        self.assertIn(workflow_name, script)
        self.assertIn("import bpy", script)
        self.assertIn("def main():", script)
        self.assertIn("log_scene_state", script)
        self.assertIn("setup_development_environment", script)

    def test_script_template_with_description(self):
        """Test that script templates include descriptions correctly"""
        script_name = "test_script"
        description = "A test script for demonstration purposes"
        
        template = self.cursor_integration.create_blender_script_template(
            script_name, description
        )
        
        # Check that template contains the description
        self.assertIn(description, template)
        self.assertIn(script_name, template)
        self.assertIn("import bpy", template)


if __name__ == "__main__":
    unittest.main() 