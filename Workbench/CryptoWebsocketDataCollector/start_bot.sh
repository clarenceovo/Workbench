#!/bin/bash
source /home/ubuntu/miniconda3/bin/activate workbench
export PYTHONPATH=/home/ubuntu/Project/Workbench/Workbench/
# Run the uvicorn command with your arguments.
python CryptoWebsocketDataCollector/BinanceWSCollector.py -d &
python CryptoWebsocketDataCollector/BinanceWSCollector.py -d &
python CryptoWebsocketDataCollector/BybitWSCollector.py -d &