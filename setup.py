from setuptools import setup, find_packages

setup(
    name="voicestudio-mcp-server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "websockets>=10.4",
        "python-dotenv>=1.0.0",
        "click>=8.1.3",
        "loguru>=0.7.0",
        "pydantic>=2.0.0",
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "mcp-python>=0.1.0",
        "pydub>=0.25.1",
        "soundfile>=0.12.1",
        "numpy>=1.24.0",
        "langdetect>=1.0.9",
        "jaconv>=0.3",
        "emoji>=2.2.0",
        "aiohttp>=3.8.4",
        "requests>=2.28.2",
        "cachetools>=5.3.0",
    ],
    extras_require={
        "test": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pytest-xdist>=3.5.0",
            "locust>=2.24.0",
            "httpx>=0.27.0",
        ],
    },
    python_requires=">=3.8",
) 