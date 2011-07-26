#!/bin/sh 
mkdir foo
cd foo
echo "made directory ./foo/ and changed to it"
virtualenv .aspen
source .aspen/bin/activate
pip install ../
echo Greetings, program! > index.html
aspen
