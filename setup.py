from setuptools import setup
setup(
    name="micro-agent",
    version="0.2.0",
    py_modules=[],
    packages=["micro_agent", "micro_agent.tools", "micro_agent.compact", "micro_agent.tui"],
    package_dir={"micro_agent": "."},
    install_requires=["openai>=1.0","python-dotenv>=1.0","requests>=2.28","beautifulsoup4>=4.12","prompt_toolkit>=3.0"],
    entry_points={"console_scripts":["micro-agent=micro_agent.tty_app:main","micro-agent-simple=micro_agent.main:main"]},
)
