#!/bin/bash
# Deploy the MCP server to the DigitalOcean VM
# Usage: ./deploy.sh

set -e

VM="openclaw"  # SSH alias for 165.22.46.178
REMOTE_DIR="/home/andy/agentic-platform"
SERVER_DIR="$(dirname "$0")"

echo "=== Deploying Agentic Platform MCP Server ==="

# 1. Create remote directory
ssh $VM "mkdir -p $REMOTE_DIR/skills $REMOTE_DIR/data"

# 2. Copy server files
scp "$SERVER_DIR/server.py" "$VM:$REMOTE_DIR/"
scp "$SERVER_DIR/auth.py" "$VM:$REMOTE_DIR/"
scp "$SERVER_DIR/requirements.txt" "$VM:$REMOTE_DIR/"
scp "$SERVER_DIR/skills/__init__.py" "$VM:$REMOTE_DIR/skills/"
scp "$SERVER_DIR/skills/governance.py" "$VM:$REMOTE_DIR/skills/"
scp "$SERVER_DIR/skills/agentic_economics.py" "$VM:$REMOTE_DIR/skills/"
scp "$SERVER_DIR/skills/intent_architecture.py" "$VM:$REMOTE_DIR/skills/"

# 3. Install dependencies on VM
ssh $VM "cd $REMOTE_DIR && python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements.txt"

# 4. Copy systemd service file
scp "$SERVER_DIR/agentic-platform.service" "$VM:/tmp/"
ssh $VM "sudo mv /tmp/agentic-platform.service /etc/systemd/system/ && sudo systemctl daemon-reload"

# 5. Start/restart the service
ssh $VM "sudo systemctl restart agentic-platform && sudo systemctl enable agentic-platform"

# 6. Check status
sleep 2
ssh $VM "sudo systemctl status agentic-platform --no-pager"

echo ""
echo "=== Deployed ==="
echo "Server running at http://165.22.46.178:8080/mcp"
echo "Next: register on MCP directories (Glama, MCP.so)"
