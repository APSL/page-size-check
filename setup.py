import os
import re
import codecs

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = codecs.open(os.path.join(package, '__init__.py'), encoding='utf-8').read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(1)


def get_author(package):
    """
    Return package author as listed in `__author__` in `init.py`.
    """
    init_py = codecs.open(os.path.join(package, '__init__.py'), encoding='utf-8').read()
    return re.search("^__author__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(1)


def get_email(package):
    """
    Return package email as listed in `__email__` in `init.py`.
    """
    init_py = codecs.open(os.path.join(package, '__init__.py'), encoding='utf-8').read()
    return re.search("^__email__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(1)


setup(
    name='page-size-check',
    version=get_version('page_size_check'),
    description='Utility to check the size of pages from a sitemap and its resources parsering the HAR file of request',
    long_description=codecs.open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8').read(),
    author=get_author('page_size_check'),
    author_email=get_email('page_size_check'),
    maintainer=get_author('page_size_check'),
    maintainer_email=get_email('page_size_check'),
    license='MIT',
    url='https://github.com/APSL/page-size-check',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4==4.6.3',
        'browsermob-proxy==0.8.0',
        'click==6.7',
        'haralyzer==1.5.0',
        'selenium==3.14.0',
        'xvfbwrapper==0.2.9',
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
