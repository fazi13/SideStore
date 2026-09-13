#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "Dependencies" / "minimuxer" / "DeviceGateway" / "idevice" / "IdeviceGateway.swift"

def main():
    if not TARGET.exists():
        print(f"Target file does not exist: {TARGET}", file=sys.stderr)
        return 1

    content = TARGET.read_text(encoding="utf-8")
    if "Holding parent lockdown session" in content:
        print("Minimuxer IdeviceGateway.swift is already patched.")
        return 0

    target_anchor = "        var client: OpaquePointer? = nil"
    patch_block = """        var parentLockdownClient: OpaquePointer? = nil
        if serviceName != "lockdownd" {
            debugLog("[IdeviceGateway] Holding parent lockdown session for child service: \\(serviceName)")
            let parentErr = lockdownd_connect(provider, &parentLockdownClient)
            if let parentErr = parentErr {
                let msg = self.getErrorMessage(from: parentErr)
                debugLog("[IdeviceGateway] warning: Failed to acquire parent lockdown session for \\(serviceName): \\(msg)")
                safeFreeError(parentErr)
            }
        }
        defer {
            if let parent = parentLockdownClient {
                verboseLog("[IdeviceGateway] Releasing parent lockdown session for \\(serviceName)")
                lockdownd_client_free(parent)
            }
        }

        var client: OpaquePointer? = nil"""

    if target_anchor not in content:
        print(f"Error: could not find anchor in {TARGET}", file=sys.stderr)
        return 1

    new_content = content.replace(target_anchor, patch_block, 1)
    TARGET.write_text(new_content, encoding="utf-8")
    print("Successfully patched minimuxer IdeviceGateway.swift.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
