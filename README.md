# dsnrun

Ad hoc utility to rerun a Python script, but with the `sentry_sdk` initialized
to a specific DSN.

Bring the awesome experience of your error tracking software to ad hoc scripts
and tools, non-production scripts and scripts that you cannot easily edit.

### Installation & Usage

```
$ pip install dsnrun
[...]

$ dsnrun -h
Usage: dsnrun [dsn] [-m module | filename] [args...]
```

To use this, just rewrite your python invocations, i.e.

```
#!bash
# normal Python
$ python -m failingmodule
[..stacktrace..]

# becomes
$ dsnrun -m failingmodule
```

```
#!bash
# normal Python
$ python /tmp/failingmodule.py
[..stacktrace..]

# becomes
$ dsnrun /tmp/failingmodule.py
```

Now, visit your Error Tracker and get a much prettier stacktrace (including
local variables).

### Rationale

At Bugsink, we like our Error Tracking so much, that we even use it for local
development. (Why wouldn't we: setup is trivial).

If you like Python, you probably do a lot with Python, including things for
which you dind't plan on setting up your Error Tracker. Still, you occasionally
mess up, leading to a stack trace on-screen.

What if that stacktrace was as awesome as the one in your error tracker?

### Features

* Because we use `runpy` to run the script, it should work with any Python
  script that you can run with `python -m` or `python filename.py`. i.e. any
  `if __name__ == '__main__':` block will still work as expected.

### Limitations

Don't use this to set up `sentry_dsn` for your actual production code. We
shouldn't have to explain why, but the gist of it is: There may very well be
edge cases that trip this thing up, and why would you break production if you
can just add a few lines to your actual production code?

These are _current_ limitations, meaning we might as well improve the script
if it turns out to be useful:

* the on-screen (printed) stacktrace for `dsnrun` is not equal to the
  regular-python version; it also contains `dsnrun` itself and the functions
  it invokes. The event as sent to your DSN does not contain these though (we
  prune it).

* `dsn` is the only currently supported argument to `sentry_sdk.init`. For
  future versions I'll put in the work of translating CLI args to SDK args.

* dsnrun manually patches `sys.argv` such that the invoked script does not
  get `dsnrun`'s arguments passed to it. This "seems to work" (but may not
  generally work). However, I did not find a way to "properly do this".
  See https://bugs.python.org/issue26388

* If you mistype the thing-to-run you'll send an `ImportError` to your DSN.
  This is not filtered out (yet). Examples:

```
ImportError: No module named nosuchmodule

FileNotFoundError: [Errno 2] No such file or directory: '/tmp/nosuchfile.py'
```
