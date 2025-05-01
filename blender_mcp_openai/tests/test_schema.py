"""
Tests for the schema extraction functionality.
"""

import unittest
from typing import Dict, List, Optional, Union, Any

from blender_mcp_openai.schema import extract_schema, _type_to_schema


class TestSchemaExtractor(unittest.TestCase):
    """Test the schema extractor functionality."""
    
    def test_basic_types(self):
        """Test schema extraction for basic Python types."""
        self.assertEqual(_type_to_schema(str), {"type": "string"})
        self.assertEqual(_type_to_schema(int), {"type": "integer"})
        self.assertEqual(_type_to_schema(float), {"type": "number"})
        self.assertEqual(_type_to_schema(bool), {"type": "boolean"})
        self.assertEqual(_type_to_schema(dict), {"type": "object"})
        self.assertEqual(_type_to_schema(list), {"type": "array"})
    
    def test_generic_types(self):
        """Test schema extraction for generic types."""
        # Test List[str]
        list_schema = _type_to_schema(List[str])
        self.assertEqual(list_schema["type"], "array")
        self.assertEqual(list_schema["items"], {"type": "string"})
        
        # Test Dict[str, int]
        dict_schema = _type_to_schema(Dict[str, int])
        self.assertEqual(dict_schema["type"], "object")
        self.assertEqual(dict_schema["additionalProperties"], {"type": "integer"})
    
    def test_optional_types(self):
        """Test schema extraction for Optional types."""
        # Test Optional[str]
        optional_schema = _type_to_schema(Optional[str])
        self.assertEqual(optional_schema["type"], ["string", "null"])
        
        # Test Optional[int]
        optional_schema = _type_to_schema(Optional[int])
        self.assertEqual(optional_schema["type"], ["integer", "null"])
    
    def test_union_types(self):
        """Test schema extraction for Union types."""
        # Test Union[str, int]
        union_schema = _type_to_schema(Union[str, int])
        self.assertEqual(union_schema["oneOf"], [{"type": "string"}, {"type": "integer"}])
    
    def test_nested_types(self):
        """Test schema extraction for nested types."""
        # Test List[Dict[str, Any]]
        nested_schema = _type_to_schema(List[Dict[str, Any]])
        self.assertEqual(nested_schema["type"], "array")
        self.assertEqual(nested_schema["items"]["type"], "object")
        
        # Test Optional[List[str]]
        optional_list_schema = _type_to_schema(Optional[List[str]])
        self.assertEqual(optional_list_schema["oneOf"][0]["type"], "array")
        self.assertEqual(optional_list_schema["oneOf"][0]["items"], {"type": "string"})
    
    def test_extract_schema(self):
        """Test extracting schema from a function."""
        def test_func(ctx, name: str, count: int, items: List[str] = None, options: Dict[str, Any] = None):
            """
            Test function for schema extraction.
            
            Args:
                ctx: The context object
                name: A string parameter
                count: An integer parameter
                items: An optional list of strings
                options: An optional dictionary of options
            """
            pass
        
        schema = extract_schema(test_func)
        
        # Check properties
        self.assertIn("name", schema["properties"])
        self.assertIn("count", schema["properties"])
        self.assertIn("items", schema["properties"])
        self.assertIn("options", schema["properties"])
        
        # Check types
        self.assertEqual(schema["properties"]["name"]["type"], "string")
        self.assertEqual(schema["properties"]["count"]["type"], "integer")
        
        # Check required fields
        self.assertIn("name", schema["required"])
        self.assertIn("count", schema["required"])
        self.assertNotIn("items", schema["required"])
        self.assertNotIn("options", schema["required"])
        
        # Check descriptions
        self.assertIn("description", schema["properties"]["name"])
        self.assertIn("description", schema["properties"]["count"])


if __name__ == "__main__":
    unittest.main() 