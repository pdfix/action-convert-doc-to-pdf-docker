#!/bin/bash

# Development unit tests. They mock LibreOffice, so they run on any machine with Python 3.12+.

set -e

pushd "$(dirname $0)/.." > /dev/null

if [ ! -d tests/venv ]; then
    python3 -m venv tests/venv
fi
tests/venv/bin/pip install --quiet -r requirements.txt
tests/venv/bin/python3 -m unittest discover -s tests -v

popd > /dev/null
