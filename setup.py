from setuptools import setup, find_packages

setup(
    name="agentsim",
    version="0.1",
    packages=find_packages(),
    install_requires=["numpy", "pyglet", "pubsub", "scikit-learn", "networkx"],
    author="Kamichanw",
    author_email="865710157@qq.com",
    description="A Python library for simulating multi-agent environments",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kami-chanw/agentsim",
)
