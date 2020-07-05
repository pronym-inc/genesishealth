#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"

"$DIR"/createDatabase.sh
"$DIR"/setupVirtualenv.sh
"$DIR"/installPipRequirements.sh
"$DIR"/migrateDatabase.sh
"$DIR"/installFixtures.sh
"$DIR"/configureLocalDns.sh
