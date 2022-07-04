"""
Treys: A pure Python poker hand evaluation library
"""

from setuptools import setup, find_packages


setup(
    name='quads',
    version='0.1.8',
    description='Quads is a pure Python poker hand evaluation library',
    long_description=open('README.rst').read(),
    author='Will Drevo, Mark Saindon, Imran Hendley, Enkhist',
    url='https://github.com/enkhist/quads',
    license='MIT',
    packages=find_packages(include=['quads', 'quads.*']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Games/Entertainment'
    ]
)
