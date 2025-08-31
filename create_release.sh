#!/bin/bash

# GitHub Release Creation Script for ConnecTUM
# Release: Version 1 (presentation)
# Tag: v1.2-stable

set -e

# Configuration
REPO_OWNER="CPSCourse-TUM-HN"
REPO_NAME="connecTUM"
TAG_NAME="v1.2-stable"
RELEASE_NAME="Version 1 (presentation)"
RELEASE_NOTES_FILE="RELEASE_NOTES.md"

echo "=== ConnecTUM Release Creation Script ==="
echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "Tag: ${TAG_NAME}"
echo "Release Name: ${RELEASE_NAME}"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d ".git" ]; then
    echo "Error: This script must be run from the root of the ConnecTUM repository"
    exit 1
fi

# Check if tag exists locally
echo "Checking if tag ${TAG_NAME} exists..."
if ! git tag -l | grep -q "^${TAG_NAME}$"; then
    echo "Error: Tag ${TAG_NAME} not found locally. Please fetch tags first:"
    echo "  git fetch --tags"
    exit 1
fi

# Get tag information
TAG_COMMIT=$(git rev-parse ${TAG_NAME})
echo "Tag ${TAG_NAME} points to commit: ${TAG_COMMIT}"

# Check if release notes file exists
if [ ! -f "${RELEASE_NOTES_FILE}" ]; then
    echo "Error: Release notes file ${RELEASE_NOTES_FILE} not found"
    exit 1
fi

echo ""
echo "=== Release Information ==="
echo "Tag: ${TAG_NAME}"
echo "Commit: ${TAG_COMMIT}"
echo "Release Name: ${RELEASE_NAME}"
echo "Release Notes: ${RELEASE_NOTES_FILE}"
echo ""

# Check GitHub CLI authentication
echo "Checking GitHub CLI authentication..."
if ! gh auth status >/dev/null 2>&1; then
    echo "Warning: GitHub CLI not authenticated."
    echo "To authenticate, run: gh auth login"
    echo ""
    echo "=== Manual Release Creation Instructions ==="
    echo "Since GitHub CLI is not authenticated, please create the release manually:"
    echo ""
    echo "1. Go to: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases"
    echo "2. Click 'Create a new release'"
    echo "3. Choose tag: ${TAG_NAME}"
    echo "4. Set release title: ${RELEASE_NAME}"
    echo "5. Copy content from ${RELEASE_NOTES_FILE} as description"
    echo "6. Mark as stable release (not pre-release)"
    echo "7. Publish release"
    echo ""
    exit 1
fi

# Create release using GitHub CLI
echo "Creating release using GitHub CLI..."
gh release create "${TAG_NAME}" \
    --title "${RELEASE_NAME}" \
    --notes-file "${RELEASE_NOTES_FILE}" \
    --repo "${REPO_OWNER}/${REPO_NAME}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Release created successfully!"
    echo "Release URL: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/tag/${TAG_NAME}"
else
    echo ""
    echo "❌ Failed to create release"
    exit 1
fi

echo ""
echo "=== Release Creation Complete ==="