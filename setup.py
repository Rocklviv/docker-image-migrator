import os
from setuptools import setup
from src.dim import __version__


def read():
    """
    Reads file and return the content of file.
    :param file: Filename to read.
    :return:
    """
    return open(os.path.join(os.path.dirname(__file__), "README.md")).read()

setup(
    name = "DIM - Docker image migrator",
    version = __version__,
    author = "Denys Chekirda",
    author_email = "",
    description = "DIM - migrates docker image from legacy (v1) registry to (v2) or AWS ECR.",
    license = "GNU GPL v3",
    keywords = "docker, cli, dim, registry, aws, ecr, elastic container repository, docker registry",
    url = "",
    packages = ["dim"],
    long_description = read(),
    classifiers= [
        "Development Status :: %s - Release" % __version__,
        "Topic :: Utilities",
        "Licence :: GNU GPL v3"
    ],

    entry_points = """
        [console_scripts]
        dim = src.dim:main
        """
)