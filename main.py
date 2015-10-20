#!/usr/bin/env python
import parse8xp
import sys
import logging

if len(sys.argv) != 3:
    print("Usage: python main.py input.8xp output.txt")
    print("       python main.py input.txt output.8xp")
    print(" (extensions other than 8xp are treated as source)")
    sys.exit(1)

source, dest = sys.argv[1:]
if source.lower().endswith(".8xp"):
    parse8xp.decompile(source, dest)
else:
    # source to 8xp
    parse8xp.recompile(source, dest)
