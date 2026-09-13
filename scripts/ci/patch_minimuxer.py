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
    fn_marker = "func performWithTcpService<T>("
    fn_idx = content.find(fn_marker)
    if fn_idx == -1:
        print(f"Error: could not find {fn_marker} in {TARGET}", file=sys.stderr)
        return 1

    next_fn_idx = content.find("func performWithEitherService<T>(", fn_idx)
    section = content[fn_idx:next_fn_idx] if next_fn_idx != -1 else content[fn_idx:]

    if "Holding parent lockdown session" in section:
        print("Minimuxer performWithTcpService in IdeviceGateway.swift is already patched.")
        return 0

    anchor = "        var client: OpaquePointer? = nil"
    client_idx = content.find(anchor, fn_idx)
    if client_idx == -1 or (next_fn_idx != -1 and client_idx > next_fn_idx):
        print(f"Error: could not find anchor inside performWithTcpService in {TARGET}", file=sys.stderr)
        return 1

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

    new_content = content[:client_idx] + patch_block + content[client_idx + len(anchor):]
    TARGET.write_text(new_content, encoding="utf-8")
    print("Successfully patched minimuxer IdeviceGateway.swift.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
