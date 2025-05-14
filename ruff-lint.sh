#!/bin/bash

if [ "$1" = "--check" ]; then
    uvx ruff check
elif [ "$1" = "--summary" ]; then
    uvx ruff check --statistics
else
    uvx ruff check --fix
fi
exit