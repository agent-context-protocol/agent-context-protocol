from setuptools import setup, find_packages

setup(
    name="agent_context_protocol",
    version="0.1.0",
    description="A multi agent communication toolkit.",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "streamlit",
        "openai",
        "tiktoken",
        "pyvis",
        "mcp",  
        "matplotlib",
        "pyyaml"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        "agent_context_protocol.prompts": ["*.txt"],
        "agent_context_protocol.prompts.agent": ["*.txt"],
        "agent_context_protocol.prompts.dag_compiler": ["*.txt"],
        "agent_context_protocol.external_env_details": ["*.json", "*.yaml", "*.yml"],
    },
)
