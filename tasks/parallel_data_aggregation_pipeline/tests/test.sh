#!/bin/bash
# Install pytest into system Python so it shares imports with the agent's
# scripts (flyte etc. were pip3-installed system-wide in the Dockerfile).
# Use --ignore-installed because Debian's apt-installed pluggy/pytest can't
# be uninstalled by pip; this just shadows them via /usr/local site-packages.
pip3 install --break-system-packages --ignore-installed \
  pluggy pytest==8.4.1 pytest-json-ctrf==0.3.5 pochi-verifier

python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_final_state.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
