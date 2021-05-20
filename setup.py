from setuptools import setup

with open("README.md", "r") as r:
    long_description = r.read()

setup(
    name='chessratings',
    version='0.0.1',
    description='Various chess rating systems',
    py_modules=['uscf_elo'],
    package_dir={'': 'src'},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Games/Entertainment :: Board Games",
        "License :: OSI Approved :: MIT License",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "numpy",
        "datetime"
    ],
    extras_require={
        "dev": [
            "pytest>=3.7",
        ],
    },
    url="https://github.com/RoaldSchuring/chessratings",
    author="Roald Schuring",
    author_email="roald.schuring@hotmail.com"
)
