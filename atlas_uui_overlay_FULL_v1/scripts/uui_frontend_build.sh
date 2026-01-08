
#!/usr/bin/env bash
set -e
cd uui
npm install
npm run build
echo "Built to uui/dist"
