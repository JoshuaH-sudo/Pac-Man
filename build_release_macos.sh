#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

: "${APPLE_SIGN_IDENTITY:?Set APPLE_SIGN_IDENTITY to your Developer ID Application certificate.}"
: "${NOTARY_KEYCHAIN_PROFILE:?Set NOTARY_KEYCHAIN_PROFILE to your notarytool keychain profile name.}"

DIST_DIR="$ROOT_DIR/dist/pac-man"
MAIN_BINARY="$DIST_DIR/pac-man"
RELEASE_DIR="$ROOT_DIR/release"
DMG_PATH="$RELEASE_DIR/pac-man-macos.dmg"

require_command() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required command: $cmd" >&2
        exit 1
    fi
}

is_macho_binary() {
    local candidate="$1"
    file -b "$candidate" | grep -q "Mach-O"
}

sign_binary() {
    local target="$1"
    codesign \
        --force \
        --sign "$APPLE_SIGN_IDENTITY" \
        --options runtime \
        --timestamp \
        "$target"
}

require_command codesign
require_command xcrun
require_command hdiutil
require_command ditto
require_command file
require_command find

if [[ ! -x "$ROOT_DIR/build_package.sh" ]]; then
    echo "build_package.sh is missing or not executable." >&2
    exit 1
fi

echo "Building package payload..."
"$ROOT_DIR/build_package.sh"

if [[ ! -x "$MAIN_BINARY" ]]; then
    echo "Expected executable not found: $MAIN_BINARY" >&2
    exit 1
fi

echo "Signing Mach-O files in packaged payload..."
while IFS= read -r -d '' file_path; do
    if is_macho_binary "$file_path"; then
        sign_binary "$file_path"
    fi
done < <(find "$DIST_DIR" -type f -print0)

echo "Verifying code signature..."
codesign --verify --deep --strict --verbose=2 "$MAIN_BINARY"

rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

echo "Creating DMG artifact..."
hdiutil create \
    -volname "Pac-Man" \
    -srcfolder "$DIST_DIR" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

echo "Submitting DMG for notarization..."
xcrun notarytool submit "$DMG_PATH" \
    --keychain-profile "$NOTARY_KEYCHAIN_PROFILE" \
    --wait

echo "Stapling notarization ticket to DMG..."
xcrun stapler staple "$DMG_PATH"

echo "Validating stapled ticket..."
xcrun stapler validate "$DMG_PATH"

echo "Release artifact ready: $DMG_PATH"
