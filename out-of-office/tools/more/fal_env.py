"""Make FAL_KEY available to fal_client on the Mac.

Keep it as `export FAL_KEY="..."` in ~/.zshrc (never type or print it in a script). A session started
before it was set won't have it in its environment, so fall back to asking a login shell. The value is only placed in this
process's environment, never printed.
"""
import os
import subprocess

if not os.environ.get("FAL_KEY"):
    k = subprocess.run(["zsh", "-ilc", 'printf %s "$FAL_KEY"'], capture_output=True, text=True).stdout.strip()
    if k:
        os.environ["FAL_KEY"] = k
