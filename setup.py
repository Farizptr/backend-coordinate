#!/usr/bin/env python3
"""
Setup script for Building Detector package.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="building-detector",
    version="1.0.0",
    author="Building Detector Team",
    author_email="your-email@example.com",
    description="A production-ready tool for detecting buildings in satellite/aerial imagery using YOLOv8",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/building-detector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "building-detector=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.geojson"],
        "examples": ["*.geojson", "*.md"],
        "docs": ["*.md"],
    },
    keywords="building detection, satellite imagery, yolo, computer vision, gis",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/building-detector/issues",
        "Documentation": "https://github.com/yourusername/building-detector/docs",
        "Source": "https://github.com/yourusername/building-detector",
    },
) 