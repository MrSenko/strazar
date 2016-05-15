#!/bin/bash

flake8 strazar/__init__.py && \
coverage run --source strazar/ --branch -m unittest discover strazar/ -v && \
coverage report -m
