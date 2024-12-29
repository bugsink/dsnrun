#!/usr/bin/env python
import os
import sys
import runpy

import sentry_sdk


def hide_dsnrun(event, hint):
    # We hide the dsnrun (and associated) frames from the stacktrace. This makes it so that the stacktrace as it shows
    # up in your error-tracker is the same as if you ran the script directly.
    #
    # NOTE: an alternative solution is to wrap a try/catch around the run_module/run_path calls and do a
    # capture_exception from there; that would perhaps also be a good way to ensure that the on-screen error message
    # matches the "run script directly" error message.

    try:
        stacktrace = event["exception"]["values"][-1]["stacktrace"]
        frames = stacktrace["frames"]

        seen = False
        for i, frame in enumerate(frames):
            if frame["filename"] == "runpy.py":
                seen = True
            if seen and frame["filename"] != "runpy.py":

                # if we have seen the runpy.py frame, and the next frame is not runpy.py, we can remove the frames
                # before that.
                stacktrace["frames"] = stacktrace["frames"][i:]
                break

    except Exception as e:
        print(f"Failed to remove dsnrun frames: {e}")

    return event


def _safe_pop(args, failure_msg):
    try:
        return args.pop(0)
    except IndexError:
        print(failure_msg)
        sys.exit(1)


def main():
    args = sys.argv[1:]  # remove the script name

    if len(args) == 0 or args[0] in ("-h", "--help"):
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

        # "<run_path>" is the module name of the main script when we run it runpy.run_path. It's safe to say it should
        # be in_app, because it's the very thing we care about.
        # when we run with -m (runpy.run_module), the module is "__main__", but we don't need to add that to the
        # in_app_include list, because the sentry_sdk will automatically pick it up with that name.
        in_app_include=["<run_path>"],
    )

    arg = _safe_pop(args, "No module or filename provided.")
    if arg == "-m":
        module = _safe_pop(args, "No module provided after -m")
        sys.argv = [module] + args  # "as good as it gets"
        runpy.run_module(module, run_name="__main__")
    else:
        sys.argv = [arg] + args
        runpy.run_path(arg, run_name="__main__")


if __name__ == "__main__":
    main()
