#!/bin/bash

hugo

pip install --upgrade pip
pip install -r requirements.txt

gunicorn app:app