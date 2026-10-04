"""Make FAL_KEY available to fal_client.

Set FAL_KEY in the environment, or keep it as `export FAL_KEY="..."` in ~/.zshrc (never type or print it in a session). A session
started before it was set won't have it in its environment, so fall back to asking a zsh login shell. The value is only placed in
this process's environment, never printed.
"""
import os
import subprocess

if not os.environ.get("FAL_KEY"):
    try:
        k = subprocess.run(["zsh", "-ilc", 'printf %s "$FAL_KEY"'], capture_output=True, text=True).stdout.strip()
    except OSError:  # no zsh on this machine: set FAL_KEY in the environment instead
        k = ""
    if k:
        os.environ["FAL_KEY"] = k
