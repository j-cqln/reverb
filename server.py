"""
server.py

Runs an instance of the Flask server to run the Reverb app on a specified port
"""

#!/usr/bin/env python

import sys
import argparse

from reverb import app

def get_args():
    """Returns command line arguments specifying port."""
    parser = argparse.ArgumentParser(description="Reverb application")

    parser.add_argument("port", type=int, help="the port at which the server should listen")

    args = parser.parse_args()

    return args.port

def main():
    """Main function for the server."""
    port = get_args()

    try:
        app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
    