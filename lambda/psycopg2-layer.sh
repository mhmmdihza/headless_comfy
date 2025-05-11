#!/bin/bash

# source : https://medium.com/@bloggeraj392/creating-a-psycopg2-layer-for-aws-lambda-a-step-by-step-guide-a2498c97c11e

set -e  # Exit immediately if a command exits with a non-zero status

# Create directory structure
mkdir -p psycopg2-layer/python

# Change into the directory
cd psycopg2-layer/python

# Install psycopg2-binary with specified platform and python version
pip3 install --platform manylinux2014_x86_64 \
             --target . \
             --python-version 3.12 \
             --only-binary=:all: \
             psycopg2-binary

# Go back to psycopg2-layer directory
cd ..

# Create a zip file of the 'python' folder
zip -r psycopg2-layer.zip python
