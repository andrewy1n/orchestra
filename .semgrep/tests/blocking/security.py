# ruff: noqa: ERA001, SIM115, UP031, UP032

import asyncio
import io
import json
import marshal
import os
import pickle
import shelve
import subprocess

import dill
import yaml


def deserialize(data: bytes, path: str) -> None:
    # ruleid: orchestra.unsafe-pickle
    pickle.loads(data)
    # ruleid: orchestra.unsafe-pickle
    pickle.load(io.BytesIO(data))
    # ruleid: orchestra.unsafe-pickle
    dill.loads(data)
    # ruleid: orchestra.unsafe-pickle
    shelve.open(path)
    # ruleid: orchestra.unsafe-marshal
    marshal.loads(data)
    # ruleid: orchestra.unsafe-marshal
    marshal.load(io.BytesIO(data))
    # ruleid: orchestra.unsafe-yaml-load
    yaml.load(data)
    # ruleid: orchestra.unsafe-yaml-load
    yaml.load(data, Loader=yaml.Loader)
    # ruleid: orchestra.unsafe-yaml-load
    yaml.unsafe_load(data)
    # ruleid: orchestra.unsafe-yaml-load
    yaml.full_load(data)
    # ruleid: orchestra.unsafe-yaml-load
    yaml.load_all(data)
    # ok: orchestra.unsafe-yaml-load
    yaml.safe_load(data)
    # ok: orchestra.unsafe-yaml-load
    yaml.load(data, Loader=yaml.SafeLoader)
    # ok: orchestra.unsafe-yaml-load
    yaml.load_all(data, yaml.CSafeLoader)
    # ok: orchestra.unsafe-pickle, orchestra.unsafe-marshal
    json.loads(data)


async def commands(command: str, value: str) -> None:
    # ruleid: orchestra.shell-true
    subprocess.run(command, shell=True)
    # ruleid: orchestra.shell-true
    os.system(command)
    # ruleid: orchestra.shell-true
    os.popen(command)
    # ruleid: orchestra.shell-true
    await asyncio.create_subprocess_shell(command)
    # ruleid: orchestra.shell-string-command
    subprocess.run(f"echo {value}")
    # ruleid: orchestra.shell-string-command
    subprocess.run("echo " + value)
    # ruleid: orchestra.shell-string-command
    subprocess.run("echo %s" % value)
    # ruleid: orchestra.shell-string-command
    subprocess.run("echo {}".format(value))
    # ok: orchestra.shell-true, orchestra.shell-string-command
    subprocess.run(["echo", f"value={value}"], shell=False)
    # ok: orchestra.shell-true
    await asyncio.create_subprocess_exec("echo", value)


def approved_shell_program(command: str) -> None:
    # ok: orchestra.shell-true
    subprocess.run(command, shell=True)  # nosemgrep: orchestra.shell-true -- shell program input.
