"""
Setup configuration for Flyte 2.0 ML Platform
"""

from setuptools import setup, find_packages

setup(
    name="flyte-ml-platform",
    version="1.0.0",
    description="End-to-End Flyte 2.0 ML Platform for model training and evaluation",
    author="Flyte ML Platform",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "flytekit>=1.10.0",
        "flytekitplugins-array>=1.10.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "joblib>=1.3.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "flyte-ml-platform=workflow:main",
        ],
    },
)