import setuptools
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, '../../Desktop/ParallelCVOA-master/README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="cvoa-datalab.upo.es",  # Replace with your own username
    version="1.0.0",
    author="Data Science & Big Data Research Lab",
    author_email="datalab@upo.es",
    description="A Python Package for Hyperparameter Tuning in Machine and Deep Learning Models Based on the Coronavirus Optimization Algorithm",
    long_description="A Python Package for Hyperparameter Tuning in Machine and Deep Learning Models Based on the Coronavirus Optimization Algorithm",
    long_description_content_type="text/markdown",
    url="https://github.com/DataLabUPO/ParallelCVOA",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
    entry_points={  # Optional
        "console_scripts": [
            "cvoa = cvoa.__main__:main"
        ],
    },
)
