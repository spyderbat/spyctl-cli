#!/bin/bash

if [ "$1" = "--check" ]; then
    uvx ruff check --select I
    uvx ruff format --check
else
    uvx ruff check --select I --fix
    uvx ruff format
fi
exit