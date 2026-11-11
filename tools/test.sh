#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
${CXX:-c++} -std=c++17 -O2 -Wall -Wextra -Werror -pedantic -Iinclude tests/test.cpp -o .build/test
.build/test
