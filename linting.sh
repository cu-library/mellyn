#! /usr/bin/env bash

echo "Agreements "
pylint --load-plugins pylint_django agreements
flake8 agreements

echo ""
echo "Accounts "
pylint --load-plugins pylint_django accounts
flake8 accounts

echo ""
echo "Mellyn "
pylint --load-plugins pylint_django mellyn
flake8 mellyn

echo ""
echo "Checking templates for inconsistent spacing in tags"
grep -r '{%[^ ]' templates/
grep -r '[^ ]%}' templates/
grep -r '{{[^ ]' templates/
grep -r '[^ ]}}' templates/
grep -r ' | ' templates/

echo ""
echo "JSHint on static/js/main.js"
jshint static/js/main.js

echo ""
echo "stylelint on static/css/main.css"
stylelint static/css/main.css
