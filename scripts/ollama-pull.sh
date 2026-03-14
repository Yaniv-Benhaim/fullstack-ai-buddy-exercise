#!/bin/bash
# Start ollama server in background and pull the tinyllama model
ollama serve &
sleep 5
ollama pull tinyllama
# Keep the server running in the foreground
wait
