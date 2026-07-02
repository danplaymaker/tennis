#!/bin/bash
cd ~/tennis
source venv/bin/activate
export TENNIS_API_KEY=91c5c1c6c9c6d54a5089d059af897a037a0add86db31802d6e6f66ba8dce0d5a
python3 -m src.cli --dashboard "$@"
