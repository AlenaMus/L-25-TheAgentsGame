"""
Setup script for Player Agent P01.
Makes the agent installable as a package.
"""

from setuptools import setup, find_packages

setup(
    name="player-agent-p01",
    version="1.0.0",
    description="Player Agent for Even/Odd League Tournament",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.2",
        "loguru>=0.7.2",
        "python-dotenv>=1.0.0",
        "pydantic-settings>=2.1.0",
        "numpy>=1.26.2",
        "scipy>=1.11.4",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.7.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "player-p01=player_agent.main:main",
        ]
    },
)
