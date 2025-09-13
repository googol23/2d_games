#!/bin/bash

GAME="world_sim.py"


wt.exe bash -c "source /.venv/bin/activate; python3 $GAME; echo '$GAME has exited. Press Enter to close...'; read"
