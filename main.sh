#! /bin/sh

if [ -d ".env" ];
then
    echo "Enabling virtual env"
else
    echo "No virtual env. Please run setup.sh first"
    exit N
fi

. .env/bin/activate
export FLASK_ENV=development
export FLASK_SECRET=3e18e8d4a243a42f4715d848614776c6483dc1108ac5fe02cfd1b98089707dcc
export SECURITY_SECRET=b5b0b9d6c02719d6dfa0197ffaee1d3bd5244cc80236562653fc13ee8349b169
python3 app.py
deactivate