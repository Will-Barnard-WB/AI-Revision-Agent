#!/bin/bash
cd /Users/willbarnard/Documents/RevisionAgent
/opt/homebrew/bin/python3.11 -m uvicorn server:app --host 0.0.0.0 --port 8080
