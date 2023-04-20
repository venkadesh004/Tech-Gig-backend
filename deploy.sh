#!/bin/bash

hugo

python -m pip install -q --upgrade pip
pip install -r requirements.txt