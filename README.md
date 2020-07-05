# Netzwerkprogrammierung 2020

Project for the Netzwerkprogrammierung course.
Service to determine who is the master in a pool of servers.

This project is developed and tested with Python 3.8.2.

## Setup

* Clone this repository and `cd` into project root.
* `pip3 install -r requirements.txt`

## Starting the service

After cloning the repository the service can be executed by running the following command in the project root:

```shell script
python3 -m netzwerkprogrammierung [-h] [--host HOST] [--port PORT] [--searchlist SEARCHLIST] [--masterscript MASTERSCRIPT] [--slavescript SLAVESCRIPT]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host the service is started on. Default: localhost
  --port PORT           Host the service is started on. Default: 7500
  --searchlist SEARCHLIST
                        Comma-seperated list of possible hosts with ports for autodetection of peer services. Example: 'localhost:1234,localhost:4567' Default: Empty list
  --masterscript MASTERSCRIPT
                        Script that will be executed by the new master after the master changes. Default: masterscript.sh
  --slavescript SLAVESCRIPT
                        Script that will be executed by every slave after the master changes. Default: slavescript.sh
```

## Example

To run the service on multiple controllers and for automatic detection of running peer services
the peer addresses and ports need to defined in the start parameters.

For testing purposes the service can be started on multiple ports on a single computer:

```shell script
python3 -m netzwerkprogrammierung --host localhost --port 7500 --searchlist localhost:7501,localhost:7502
```

```shell script
python3 -m netzwerkprogrammierung --host localhost --port 7501 --searchlist localhost:7500,localhost:7502
```

```shell script
python3 -m netzwerkprogrammierung --host localhost --port 7502 --searchlist localhost:7501,localhost:7500
```

## Documentation

A current HTML version of the PyDoc documentation is available as an artifact of the docs build job.

The documentation is also published on gitlab pages [here](http://jpohlmeyer.pages.ub.uni-bielefeld.de/netzwerkprogrammierung-2020/netzwerkprogrammierung/).

It can further be build locally with the following command:

```shell script
pdoc3 --html -o docs netzwerkprogrammierung
```

## Tests

The unit tests can be found in the tests package and can be run with the following command:

```shell script
python3 -m unittest discover
```