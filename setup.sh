#!/usr/bin/env bash
#
# garnish setup script - Simple environment setup
#

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🥄 Garnish Development Environment Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}UV not found. Please install UV first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    uv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate virtual environment
source .venv/bin/activate

# Install garnish with dependencies
echo -e "${BLUE}Installing garnish...${NC}"
uv pip install -e .
echo -e "${GREEN}✅ Garnish installed${NC}"

# Install dev dependencies if requested
if [ "$1" == "--dev" ]; then
    echo -e "${BLUE}Installing development dependencies...${NC}"
    uv pip install -e ".[dev]"
    echo -e "${GREEN}✅ Development dependencies installed${NC}"
fi

# Install sibling packages if they exist
echo -e "${BLUE}Checking for sibling packages...${NC}"
for pkg in pyvider-components pyvider-cty pyvider-hcl pyvider-rpcplugin pyvider-telemetry; do
    if [ -d "../$pkg" ]; then
        echo "  Installing $pkg..."
        uv pip install -e "../$pkg"
        echo -e "  ${GREEN}✅ $pkg installed${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Environment activated. Commands available:"
echo "  garnish --help    # Show garnish commands"
echo "  pytest            # Run tests (if dev dependencies installed)"
echo "  deactivate        # Exit virtual environment"
echo ""
echo "To activate this environment again:"
echo "  source .venv/bin/activate"