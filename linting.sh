#! /usr/bin/env bash

echo "---Agreements---"
pylint --load-plugins pylint_django agreements
flake8 agreements

echo ""
echo "---Accounts---"
pylint --load-plugins pylint_django accounts
flake8 accounts

echo ""
echo "---Mellyn---"
pylint --load-plugins pylint_django mellyn
flake8 accounts
