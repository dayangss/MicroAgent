from setuptools import setup, find_packages
setup(
    name="micro-agent",
    version="0.2.0",
    packages=find_packages(include=["micro_agent", "micro_agent.*"]),
    install_requires=[
        "openai>=1.0",
        "python-dotenv>=1.0",
        "requests>=2.28",
        "beautifulsoup4>=4.12",
        "prompt_toolkit>=3.0",
    ],
    entry_points={
        "console_scripts": [
            "micro-agent=micro_agent.tty_app:main",
            "micro-agent-simple=micr