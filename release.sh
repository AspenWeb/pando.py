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
        if [ "$proceed" = "n" -o "$proceed" = "N" -o "$proceed" = "" ]
        then
            return 1
        fi
    done
    return 0
}

# Real work.
if [ -z "$1" ]; then
    echo "Specify a version to release."
    exit 1
elif [ "`git tag | grep $1`" ]; then
    echo "Version $1 is already git tagged."
elif [ "x`wheel version | cut -f 1 -d' '`" != "xwheel" ]; then
    echo "You need to 'pip install wheel'"
    exit 1
else
    confirm "Did you add to the Changelog?"
    if [ $? -ne 0 ]; then
        echo "Go do that first."
        exit 1
    fi
    confirm "Tag version $1 and upload to PyPI and push to github and heroku?"
    if [ $? -eq 0 ]; then
        printf "$1" > version.txt
        git commit version.txt -m"Release $1"
        git tag $1

        git push
        git push --tags

        python setup.py sdist --formats=zip,gztar,bztar upload
        python setup.py bdist_wheel upload

        printf "\055dev" >> version.txt
        git commit version.txt -m"Bump version to $1-dev"
        git push
        git push heroku

        rm -rf dist
    fi
fi
