#! /bin/sh
if [ -d ".env" ];
then
    echo ".env folder exists. Installing using pip"
else
    echo "creating .env and installing using pip"
    python3 -m venv .env
fi

# Activate Virual Environment
. .env/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

deactivate