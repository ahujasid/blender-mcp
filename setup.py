from setuptools import setup, find_packages

setup(
    name="blender-mcp-openai",
    version="0.1.0",
    description="OpenAI adapter for BlenderMCP",
    author="BlenderMCP Community",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "blender-mcp>=1.1.0,<2.0.0",  # Compatible with version 1.1 up to (but not including) 2.0
        "jsonschema>=4.0.0",
        "docstring-parser>=0.15",  # For parsing docstrings into structured information
    ],
    entry_points={
        "console_scripts": [
            "blender-mcp-openai=blender_mcp_openai.cli:main",
            "openai_adapter=blender_mcp_openai.backward_compat:main",  # Legacy entry point
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 