# measure-noise

Measure how our data deviates from normal distribution. ([project summary](https://docs.google.com/document/d/1TMUhY4zaOA_DV6hzmNY3Z2v9Hm6XF3zlKvWOTRL4xJs/edit#))


|Branch      |Status   | Coverage |
|------------|---------|----------|
|master      | [![Build Status](https://travis-ci.org/mozilla/measure-noise.svg?branch=master)](https://travis-ci.org/mozilla/measure-noise) | |
|dev         | [![Build Status](https://travis-ci.org/mozilla/measure-noise.svg?branch=dev)](https://travis-ci.org/mozilla/measure-noise)    | [![Coverage Status](https://coveralls.io/repos/github/mozilla/measure-noise/badge.svg)](https://coveralls.io/github/mozilla/measure-noise) |


## Install

    pip install measure-noise

## Usage

The `deviance()` method will return a `(description, score)` pair describing how the samples deviate from a normal distribution, and by how much.  This is intended to screen samples for use in the t-test, and other statistics, that assume a normal distribution.

* `SKEWED` - samples are heavily to one side of the mean
* `OUTLIERS` - there are more outliers than would be expected from normal distribution
* `MODAL` - few samples are near the mean (probably bimodal)
* `OK` - no egregious deviation from normal
* `N/A` - not enough data to make a conclusion (aka `OK`)

#### Example

    from measure_noise import deviance

	>>> desc, score = deviance([1,2,3,4,5,6,7,8])
    >>> desc
    'OK'

## Development

For Linux/OSX

    git clone https://github.com/mozilla/measure-noise.git
    cd measure-noise
    python -m venv .venv      
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -r tests/requirements.txt
    export PYTHONPATH=.:vendor
    python -m unittest discover tests 

Similar for Windows:

    git clone https://github.com/mozilla/measure-noise.git
    cd measure-noise
    python.exe -m pip install virtualenv  
    python.exe -m virtualenv .venv 
    .venv\Scripts\activate
    pip install -r requirements.txt
    pip install -r tests\requirements.txt
    set PYTHONPATH=.;vendor
    python -m unittest discover tests 


---------------------

## Analysis Configuration

The analysis is controlled by the `config.json` file, but it is missing the secrets required to connect to the Treeherder RO database and BigQuery. You must provide references to secrets by making your own config file. 

Please look at the existing `resources/config-<user>.json` files. You may make a copy of one, and update it with references to the secrets on your dev machine. For example, `resources/kyle-config.json` looks like

```json
{
    "$ref": "../config.json",
    "database.$ref": "~/private.json#treeherder",
    "deviant_summary.account_info.$ref": "file:///e:/moz-fx-dev-ekyle-treeherder-a838a7718652.json",
    "constants.measure_noise.analysis.SCATTER_RANGE": "month",
    "constants.measure_noise.analysis.TREEHERDER_RANGE": "90day"
}
```

You may be able to guess where each of my secrets are found on my machine. For example, I have a `private.json` file in my user directory. Here is an example of the contents:

```javascript
// Example contents of ~/private.json
{
    "treeherder": {
        "host": "treeherder-prod-ro.cd3i3txkp6c6.us-east-1.rds.amazonaws.com",
        "port" : 3306,
        "username": "username",
        "password": "password"
    }
}
```

Feel free to add your `resources/config-<user>.json` file and make a PR with it. Remember, **never put secrets in your project directory**; use references to secrets instead.   

> You may use `{"$ref":"env://MY_ENV_VARIABLE"}` to use environment variables. [More details](https://github.com/klahnakoski/mo-json-config#environment-variables-reference) 

## Running Analysis

Ensure you are in the main project directory, and point to your config file 

**Linux/OSX**

    export PYTHONPATH=.:vendor
    python measure_noise/analysis.py --config=resources/config-<user>.json

**Windows**

    set PYTHONPATH=.;vendor
    python measure_noise\analysis.py --config=resources\config-kyle.json


Some other options are 

* `--id` - show specific signature_ids
* `--download=<filename>` - Download all deviant statistics to file
* `--deviant=<int>` - Show number of series with most deviant noise 
* `--outliers=<int>` - Show number of series with most outliers noise 
* `--modal=<int>` - Show number of series that seem bi-modal 
* `--skewed=<int>` - Show number of series where mean and median differ 
* `--ok=<int>` - Show number of series that are worst, but good enough 
* `--noise=<int>` - Show number of series with largest relative standard deviation
* `--extra=<int>` - Show number of series where Perfherder has detected steps, but not MWU
* `--missing=<int>` - Show number of series where Perfherder missed alerting

## Post Analysis

The `analysis.py` fills a local Sqlite database (as per the config file). It can be used to lookup other series that may be of interest, or to feed yet-another-program.


## Windows

You must download the `scipy` and `numpy` binary packages. 
