# Brainbro
BrainVISA in Browser

## Install brainbro
```sh
# Record base directory for later reference
base="$PWD"
virtualenv brainbro
cd brainbro
bin/pip install --upgrade pip
bin/pip install --upgrade pyramid pyramid-jinja2 pyramid-debugtoolbar paramiko waitress
git clone https://github.com/cati-neuroimaging/brainbro.git src
ln -s ../../../src/brainbro lib/python2.7/site-packages/brainbro
```
## Start brainbro web service for developement
```sh
# $base is the directory containing the brainbro directory
# created with virtualenv
$base/brainbro/bin/pserve $base/brainbro/src/development.ini 
```
Then visit [[http://localhost:6543]]