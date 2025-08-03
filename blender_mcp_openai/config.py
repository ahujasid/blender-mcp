"""
Configuration handling for the BlenderMCP OpenAI adapter.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List


@dataclass
class OpenAIConfig:
    """
    Configuration for OpenAI API calls.
    
    This class handles the configuration parameters for OpenAI API calls,
    including model selection, temperature, and other parameters.
    
    Attributes:
        model: The OpenAI model to use (default: "gpt-4")
        api_key: The OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        temperature: The sampling temperature (default: 0.7)
        max_tokens: The maximum number of tokens to generate
        top_p: The nucleus sampling parameter (default: 1.0)
        frequency_penalty: Penalty for token frequency (default: 0)
        presence_penalty: Penalty for token presence (default: 0)
        system_prompt: Optional system prompt to prepend to conversations
        additional_params: Additional parameters to pass to the OpenAI API
    """
    model: str = "gpt-4"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_prompt: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize after dataclass initialization."""
        # Use environment variable for API key if not provided
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary for API calls.
        
        Returns:
            Dictionary of parameters for OpenAI API calls
        """
        # Start with basic parameters
        result = {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        
        # Add optional parameters if set
        if self.max_tokens:
            result["max_tokens"] = self.max_tokens
        
        if self.frequency_penalty:
            result["frequency_penalty"] = self.frequency_penalty
            
        if self.presence_penalty:
            result["presence_penalty"] = self.presence_penalty
            
        # Add any additional parameters
        result.update(self.additional_params)
        
        return result
    
    def get_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare messages for an API call, including the system prompt if set.
        
        Args:
            messages: The messages provided by the user
            
        Returns:
            Messages with system prompt prepended if available
        """
        if not self.system_prompt:
            return messages
            
        # Add system prompt at the beginning
        return [{"role": "system", "content": self.system_prompt}] + messages
    
    @classmethod
    def from_file(cls, file_path: str) -> "OpenAIConfig":
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            OpenAIConfig instance with values from the file
        """
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def to_file(self, file_path: str) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            file_path: Path to save the configuration
        """
        with open(file_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)


@dataclass
class AdapterConfig:
    """
    Overall configuration for the BlenderMCP OpenAI adapter.
    
    This class combines OpenAI configuration with adapter-specific settings.
    
    Attributes:
        openai: OpenAI API configuration
        log_level: Logging level (default: "INFO")
        log_file: Optional path to a log file
        json_logging: Whether to use JSON format for logs (default: False)
        mcp_connection: Connection parameters for the MCP server
    """
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    log_level: str = "INFO"
    log_file: Optional[str] = None
    json_logging: bool = False
    mcp_connection: Dict[str, Any] = field(default_factory=lambda: {
        "host": "localhost",
        "port": 9876
    })
    
    @classmethod
    def from_file(cls, file_path: str) -> "AdapterConfig":
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            AdapterConfig instance with values from the file
        """
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
            
        # Handle nested OpenAI config if present
        if "openai" in config_dict and isinstance(config_dict["openai"], dict):
            config_dict["openai"] = OpenAIConfig(**config_dict["openai"])
            
        return cls(**config_dict)
    
    def to_file(self, file_path: str) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            file_path: Path to save the configuration
        """
        # Convert to dictionary, handling nested dataclasses
        config_dict = asdict(self)
        
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2) 