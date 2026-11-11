#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
${CXX:-c++} -std=c++17 -O1 -g -fsanitize=address,undefined -Wall -Wextra -Werror -Iinclude tests/schedule.cpp -o .build/schedule
.build/schedule
