#!/usr/bin/env python3

import argparse


def main():
    parser = argparse.ArgumentParser(description="Determine master server in a high availability cluster.")
    parser.add_argument("--host", default="localhost",
                        help="Host the service is started on.")
    parser.add_argument("--port", type=int, default="7500",
                        help="Host the service is started on.")
    parser.add_argument("--searchlist", default="localhost",
                        help="List of possible hosts for autodetection of peer services.")
    args = parser.parse_args()
    print(args)


if __name__ == "__main__":
    main()