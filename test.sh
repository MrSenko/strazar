#!/bin/bash

flake8 strazar/__init__.py && \
pylint -rn strazar tests/*.py && \
coverage run --source strazar/ --branch -m unittest discover tests/ -v && \
coverage report -m
