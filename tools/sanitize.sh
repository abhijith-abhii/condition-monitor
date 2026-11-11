#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
${CXX:-c++} -std=c++17 -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -Wall -Wextra -Werror -Iinclude tests/test.cpp -o .build/test-sanitized
.build/test-sanitized
