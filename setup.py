from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="autonomy-events",
    version="1.0.0",
    description="Production-grade shared event library for the Autonomous Company OS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Autonomous Company",
    author_email="engineering@autonomous.company",
    url="https://github.com/autonomous-company/autonomy-events",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "aio-pika>=9.0.0",
        "structlog>=23.0.0",
        "protobuf>=4.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "autonomy-events=autonomy_events.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
