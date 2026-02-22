#!/bin/bash
# Test API endpoints
echo "=== Ambient Status ==="
curl -s http://localhost:8080/ambient/status
echo
echo "=== Ambient Manifest ==="
curl -s http://localhost:8080/ambient/manifest
echo
echo "=== Outputs ==="
curl -s http://localhost:8080/outputs
echo
echo "=== Tasks ==="
curl -s http://localhost:8080/tasks
echo
echo "=== Chat Page ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8080/chat
echo
echo "=== Ambient Page ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8080/ambient
echo
echo "=== History Page ==="
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8080/history
echo
echo
echo "All tests done!"
