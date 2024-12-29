#!/usr/bin/env python
import os
import sys
import runpy

import sentry_sdk


def hide_dsnrun(event, hint):
    # TODO wrap w/ try/except: we never want to crash the app because of this
    # TODO what if _not_ found?
    # alternatively: prune while catching the exception (explicitly)
    # event['exception']['values'][1]['stacktrace']['frames']

    stacktrace = event["exception"]["values"][-1]["stacktrace"]
    frames = stacktrace["frames"]

    seen = False
    for i, frame in enumerate(frames):
        if frame["filename"] == "runpy.py":
            seen = True
        if seen and frame["filename"] != "runpy.py":
            break

    stacktrace["frames"] = stacktrace["frames"][i:]
    return event


def _safe_pop(args, msg):
    try:
        return args.pop(0)
    except IndexError:
        print(msg)
        sys.exit(1)


def main():
    args = sys.argv[1:]  # we don't need the script name

    if len(args) == 0:
        print("Usage: dsnrun [dsn] [-m module | filename] [args...]")
        sys.exit(1)

    if args[0].startswith("http"):
        SENTRY_DSN = args.pop(0)
    elif "SENTRY_DSN" in os.environ:
        SENTRY_DSN = os.environ["SENTRY_DSN"]
    else:
        print("No DSN provided; set SENTRY_DSN or pass it as the first argument.")
        sys.exit(1)

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        before_send=hide_dsnrun,
        in_app_include=["<run_path>"],  # this is the module name of the main script after we run it w/ runpy (is it for the -m case?)
    )

    arg = _safe_pop(args, "No module or filename provided.")
    if arg == "-m":
        module = _safe_pop(args, "No module provided after -m")
        sys.argv = [module] + args  # "as good as it gets"
        runpy.run_module(module, run_name="__main__")
    else:
        sys.argv = [arg] + args
        runpy.run_path(arg)


if __name__ == "__main__":
    main()
