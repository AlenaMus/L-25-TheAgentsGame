"""
Setup script for League Manager.
Makes the agent installable as a package.
"""

from setuptools import setup, find_packages

setup(
    name="league-manager",
    version="1.0.0",
    description="League Manager for Even/Odd Tournament",
    author="AI Development Course",
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
            "league-manager=league_manager.main:main",
        ]
    },
)
