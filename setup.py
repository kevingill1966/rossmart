from setuptools import setup, find_packages

setup(
    name='rossmart',
    version='0.1',
    packages=['rossmart',],
    license='Creative Commons Attribution Share Alike 4.0',
    long_description=open('README.rst').read(),
    install_requires=[
        "requests>=2.20.0",
        "requests-http-signature>=0.1.0",
        "cryptography>=2.3.1",
        # "flex>=6.13.2",
    ],
)
