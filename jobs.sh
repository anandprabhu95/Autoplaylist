#!/usr/bin/env bash

echo $(date)
echo Running jobs.sh

# spotipy_creds.sh will export spotipy credentials as environment variables.
# Create this file and place it in the same folder as jobs.sh
source /home/aprabhu3/repos/Autoplaylist/spotipy_creds.sh

# Run autoplaylist.py
cd /home/aprabhu3/repos/Autoplaylist/
python3 autoplaylist.py

