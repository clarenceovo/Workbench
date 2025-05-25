#!/bin/bash
source /home/ubuntu/miniconda3/bin/activate workbench
export PYTHONPATH=/home/ubuntu/Project/Workbench/Workbench/CryptoWebsocketDataCollector/
# Run the uvicorn command with your arguments.
python BinanceWSCollector.py -d &
python BinanceWSCollector.py -d &
python BybitWSCollector.py -d &