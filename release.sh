#!/bin/sh

# Exit on first error.
set -e

# Go to a known location: the directory where we ourselves live.
cd "`dirname $0`"

# Confirmation helper.
confirm () {
    proceed=""
    while [ "$proceed" != "y" ]; do
        read -p"$1 (y/N) " proceed
        if [ "$proceed" == "n" -o "$proceed" == "N" -o "$proceed" == "" ]
        then
            return 1
        fi
    done
    return 0
}

# Real work.
confirm "Tag version $1 and upload to PyPI?"
if [ $? -eq 0 ]; then
    printf "$1" > version.txt
    git commit version.txt -m"Version bump for release."
    git tag $1

    git push
    git push --tags

    ./env/bin/python setup.py sdist --formats=zip,gztar,bztar upload

    printf "+" >> version.txt
    git commit version.txt -m"Version bump post-release."
    git push

    rm -rf dist
fi
