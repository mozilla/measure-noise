# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    description=str(u'Measure deviant noise'),
    license=str(u'MPL 2.0'),
    author=str(u'Mozilla Perftest'),
    author_email=str(u'perftest@mozilla.com'),
    long_description_content_type=str(u'text/markdown'),
    include_package_data=True,
    classifiers=["Development Status :: 4 - Beta","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"],
    install_requires=["numpy>=1.23.1","scipy==1.10.0"],
    version=str(u'2.60.0.2'),
    url=str(u'https://github.com/mozilla/measure-noise'),
    packages=["moz_measure_noise"],
    long_description=str(u"# measure-noise\nMeasure how our data deviates from normal distribution\n\n\n|Branch      |Status   | Coverage |\n|------------|---------|----------|\n|master      | [![Build Status](https://travis-ci.org/mozilla/measure-noise.svg?branch=master)](https://travis-ci.org/mozilla/measure-noise) | |\n|dev         | [![Build Status](https://travis-ci.org/mozilla/measure-noise.svg?branch=dev)](https://travis-ci.org/mozilla/measure-noise)    | [![Coverage Status](https://coveralls.io/repos/github/mozilla/measure-noise/badge.svg)](https://coveralls.io/github/mozilla/measure-noise) |\n\n\n## Install\n\n    pip install measure-noise\n\n## Usage\n\nThe `deviance()` method will return a `(description, score)` pair describing how the samples deviate from a normal distribution, and by how much.  This is intended to screen samples for use in the t-test, and other statistics, that assume a normal distribution.\n\n* `SKEWED` - samples are heavily to one side of the mean\n* `OUTLIERS` - there are more outliers than would be expected from normal distribution\n* `MODAL` - few samples are near the mean (probably bimodal)\n* `OK` - no egregious deviation from normal\n* `N/A` - not enough data to make a conclusion (aka `OK`)\n\n#### Example\n\n    from measure_noise import deviance\n\n\t>>> desc, score = deviance([1,2,3,4,5,6,7,8])\n    >>> desc\n    'OK'\n\n## Development\n\n    git clone https://github.com/mozilla/measure-noise.git\n    cd measure-noise\n    pip install -r requirements.txt\n    pip install or tests/requirements.txt\n    python -m unittest discover tests \n\n## Windows\n\nYou must download the `scipy` and `numpy` binary packages. \n"),
    name=str(u'moz-measure-noise')
)