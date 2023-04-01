#! /usr/bin/env bash

echo "Agreements"
pylint --load-plugins pylint_django --django-settings-module=mellyn.settings agreements
flake8 agreements

echo ""
echo "Accounts"
pylint --load-plugins pylint_django --django-settings-module=mellyn.settings accounts
flake8 accounts

echo ""
echo "Mellyn"
pylint --load-plugins pylint_django --django-settings-module=mellyn.settings mellyn
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
npx jshint static/js/main.js

echo ""
echo "stylelint on static/css/main.css"
npx stylelint static/css/main.css

echo ""
echo "prettier check on static/css/main.css"
npx prettier --single-quote --check static/css/main.css
