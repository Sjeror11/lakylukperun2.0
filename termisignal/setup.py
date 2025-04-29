"""
Setup script pro TermiSignal
"""

from setuptools import setup, find_packages

setup(
    name="termisignal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "textual>=0.38.1",
        "pynacl>=1.5.0",
        "websockets>=11.0.3",
        "python-dotenv>=1.0.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "termisignal=termisignal.app.main:main",
        ],
    },
    author="Laky",
    author_email="example@example.com",
    description="Terminálová šifrovaná komunikační aplikace inspirovaná Signalem",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/termisignal",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
