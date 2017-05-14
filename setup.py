#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='terebi',
    description='a python interface to mpv',
    version="0.1.1",
    author='slowpoke',
    author_email='mail+pypi@slowpoke.io',
    url='https://github.com/slowpoketail/terebi',
    packages=[
        'terebi',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: POSIX :: Linux',
    ],
    license='ANTI-LICENSE',
)
