#! /usr/bin/env bash

rm accounts/migrations/0001_initial.py agreements/migrations/0001_initial.py db.sqlite3 && python manage.py makemigrations && python manage.py migrate && python manage.py loaddata testdata.json
