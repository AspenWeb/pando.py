#!/bin/sh 
mkdir foo
cd foo
virtualenv .aspen
source .aspen/bin/activate
pip install https://github.com/jamwt/diesel/tarball/master
pip install https://github.com/whit537/aspen/tarball/master
echo Greetings, program! > index.html
aspen
