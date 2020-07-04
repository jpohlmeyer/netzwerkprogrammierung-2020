# Netzwerkprogrammierung 2020

Project for the Netzwerkprogrammierung course.
Service to determine who is the master in a pool of servers.

## Example

After cloning the repository the service can be executed by running the following command in the project root:

```shell script
python -m netzwerkprogrammierung
```

To run the service on multiple controllers and for automatic detection of running peer services
the peer addresses and ports need to defined in the start parameters.

For testing purposes the service can be started on multiple ports on a single computer:

```shell script
python -m netzwerkprogrammierung --host localhost --port 7500 --searchlist localhost:7501,localhost:7502
```

```shell script
python -m netzwerkprogrammierung --host localhost --port 7501 --searchlist localhost:7500,localhost:7502
```

```shell script
python -m netzwerkprogrammierung --host localhost --port 7502 --searchlist localhost:7501,localhost:7500
```