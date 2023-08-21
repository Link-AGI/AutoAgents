"""wutils: handy tools
"""
import subprocess
from codecs import open
from os import path

from setuptools import Command, find_packages, setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line]

setup(
    name="autoagents",
    version="0.1",
    description="The Automatic Agents Generation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LinkSoul-AI/AutoAgents",
    author="Guangyao Chen",
    author_email="gy.chen@foxmail.com",
    license="Apache 2.0",
    keywords="autoagent multi-agent agent-generation gpt llm",
    packages=find_packages(exclude=["contrib", "docs", "examples"]),
    python_requires=">=3.9",
    install_requires=requirements,
)
