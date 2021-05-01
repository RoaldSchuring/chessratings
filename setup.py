from setuptools import setup

with open("README.md", "r") as r:
    long_description = r.read()

setup(
    name='chessratings',
    version='0.0.1',
    description='Various chess rating systems',
    py_modules=['uscf_elo'],
    package_dir={'': 'src'},
    # classifiers=https://pypi.org/classifiers/,
    long_description=long_description,
    long_description_content_type="text/markdown",
    # install_requires = [
    #     "numpy"
    # ],
    extras_require={
        "dev": [
            "pytest>=3.7",
        ],
    },
    url="https://github.com/RoaldSchuring/chess_ratings",
    author="Roald Schuring",
    author_email="roald.schuring@hotmail.com"
)
