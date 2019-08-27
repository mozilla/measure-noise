# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    description=str(u'Measure deviant noise'),
    license=str(u'MPL 2.0'),
    author=str(u'Kyle Lahnakoski'),
    author_email=str(u'kyle@lahnakoski.com'),
    long_description_content_type=str(u'text/markdown'),
    include_package_data=True,
    classifiers=["Development Status :: 4 - Beta","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"],
    install_requires=["numpy","scipy"],
    version=str(u'2.51.19239'),
    url=str(u'https://github.com/mozilla/measure-noise'),
    packages=["measure_noise"],
    long_description=str(u'# measure-noise\nMeasure how our data deviates from normal distribution\n\n\n|Branch      |Status   | Coverage |\n|------------|---------|----------|\n|master      | [![Build Status](https://travis-ci.org/mozilla/measure-noise.svg?branch=master)](https://travis-ci.org/mozilla/measure-noise) | |\n|dev         | [![Build Status](https://travis-ci.org/mozilla/measure-noise.svg?branch=dev)](https://travis-ci.org/mozilla/measure-noise)    | [![Coverage Status](https://coveralls.io/repos/github/mozilla/measure-noise/badge.svg)](https://coveralls.io/github/mozilla/measure-noise) |\n\n\n## Install\n\n    pip install measure-noise\n\n## Development\n\n    git clone https://github.com/mozilla/measure-noise.git\n    cd measure-noise\n    pip install -r requirements.txt\n    pip install or tests/requirements.txt\n    python -m unittest discover tests \n\n## Windows\n\nYou must download the `scipy` and `numpy` binary packages. \n'),
    name=str(u'measure-noise')
)