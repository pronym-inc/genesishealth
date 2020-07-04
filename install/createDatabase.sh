#!/usr/bin/env bash
echo "Creating database..."
createuser -s genesishealth || :
createdb -O genesishealth genesishealth || :