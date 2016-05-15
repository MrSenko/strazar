#!/bin/bash

flake8 src/strazar.py && \
coverage run --source src/ --branch -m unittest discover src -v && \
coverage report -m
