from setuptools import setup

setup(
    name="claw_log",
    version="0.1.3",
    packages=["claw_log"],
    package_dir={"claw_log": "."},
    install_requires=[
        "google-genai>=0.3.0",
        "openai",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "claw-log=claw_log.main:main",
        ],
    },
)
