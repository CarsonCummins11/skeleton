#!/bin/bash

# Main setup script for the project
# This script should be run by new team members when they clone the repository

set -e

echo "🚀 Setting up the project..."

# Check if we're in a Git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a Git repository"
    echo "Please run this script from the root of the Git repository"
    exit 1
fi

# Install Git hooks
if [ -f "scripts/install-git-hooks.sh" ]; then
    echo "🔧 Installing Git hooks..."
    ./scripts/install-git-hooks.sh
else
    echo "⚠️  Warning: Git hooks install script not found"
fi

# Install post-checkout and post-merge hooks for auto-installation
if [ -d "scripts/git-hooks" ]; then
    echo "🔧 Setting up auto-installation hooks..."
    
    # Install post-checkout hook
    if [ -f "scripts/git-hooks/post-checkout" ]; then
        cp scripts/git-hooks/post-checkout .git/hooks/
        chmod +x .git/hooks/post-checkout
        echo "✅ Installed post-checkout hook"
    fi
    
    # Install post-merge hook
    if [ -f "scripts/git-hooks/post-merge" ]; then
        cp scripts/git-hooks/post-merge .git/hooks/
        chmod +x .git/hooks/post-merge
        echo "✅ Installed post-merge hook"
    fi
fi

echo "🎉 Project setup completed successfully!"
echo ""
echo "📝 What was installed:"
echo "  - Git hooks for automatic backend switching"
echo "  - Auto-installation hooks for future updates"
echo ""
echo "🔧 Next steps:"
echo "  - Run 'cd tf && ./switch-backend.sh local' to use local backend for development"
echo "  - The hooks will automatically manage backend switching during commits" 