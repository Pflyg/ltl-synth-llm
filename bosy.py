import docker
from docker.errors import DockerException
import os

import requests
import syfco
from utils import rename_module

from tempfile import TemporaryDirectory


class BosyError(Exception):
    pass


try:
    client = docker.from_env()
    client.images.pull("ghcr.io/frederikschmitt/bosy:latest")
except (FileNotFoundError, DockerException):
    raise Exception("Couldn't start docker. Is docker service daemon running?")
tmp_dir = os.path.abspath(".")


def synthesize(
    spec: str,
    target: str = "verilog",
    overwrite_params: dict = {},
    timeout=60,
    module_name="fsm",
):
    """
    Runs the BoSyBackend binary from a docker container
    - spec: should be in tlsf format
    - target: aiger|dot|dot-topology|smv|verilog|all
    - overwrite_params: overwrite parameters in tlsf file
    - module_name: only used when target = verilog. Defines the verilog output module name
    - timeout: specify a timeout in seconds
    """

    # generate bosy input
    bosy_input = syfco.convert(spec, "bosy", overwrite_params=overwrite_params)
    code = synthesize_bosy(input=bosy_input, target=target, timeout=timeout)
    # we have to explicitly change the module name from the default "fsm"
    return rename_module(code, module_name, "fsm") if target == "verilog" else code


def synthesize_bosy(input: str, target: str = "verilog", timeout=60):
    """
    Runs the BoSyBackend binary from a docker container
    - target: aiger|dot|dot-topology|smv|verilog|all
    - timeout: specify a timeout in seconds
    """
    # - automaton-tool: lt3ba|spot
    # provides a tempfile
    with TemporaryDirectory() as tmp_dir:
        tmpname = ".tmp.bosy"
        tmpfile = os.path.join(tmp_dir, tmpname)

        with open(tmpfile, "w") as f:
            f.write(input)
        mount = docker.types.Mount(
            type="bind", target="/root/bosy/_mount", source=tmp_dir
        )
        container = client.containers.run(
            "ghcr.io/frederikschmitt/bosy:latest",
            mounts=[mount],
            entrypoint=".build/release/BoSyBackend",
            command="--automaton-tool spot --synthesize --target "
            + target
            + " _mount/"
            + tmpname,
            detach=True,
        )
        # this timeout code is still a bit wonky and probably unreliable, due to the docker bindings being a bit buggy
        try:
            container.wait(timeout=timeout)
            stdout = container.logs(stdout=True, stderr=False)
            stderr = container.logs(stdout=False, stderr=True)
            if isinstance(stdout, bytes):
                stdout = stdout.decode()
            if isinstance(stderr, bytes):
                stderr = stderr.decode()
            if (
                "error:" in stderr or stdout == ""
            ):  # BoSy doesn't seem to have an option to quiet info on stderr
                raise BosyError()
            return stdout
        # https://github.com/docker/docker-py/issues/1966
        except (
            TimeoutError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ):
            container.kill()
            raise TimeoutError from None


'''
synthesize_bosy(
    """{"semantics": "mealy", "inputs": ["upd", "in_0", "in_1", "in_2", "in_3"], "outputs": ["out_0", "out_1", "out_2", "out_3"], "assumptions": [], "guarantees": ["(G ((upd) -> (((((((((((((in_0) <-> (out_0)) && ((in_0) -> (X (((out_0) U (upd)) || (G (out_0)))))) && ((! (in_0)) -> (X (((! (out_0)) U (upd)) || (G (! (out_0))))))) && ((in_1) <-> (out_1))) && ((in_1) -> (X (((out_1) U (upd)) || (G (out_1)))))) && ((! (in_1)) -> (X (((! (out_1)) U (upd)) || (G (! (out_1))))))) && ((in_2) <-> (out_2))) && ((in_2) -> (X (((out_2) U (upd)) || (G (out_2)))))) && ((! (in_2)) -> (X (((! (out_2)) U (upd)) || (G (! (out_2))))))) && ((in_3) <-> (out_3))) && ((in_3) -> (X (((out_3) U (upd)) || (G (out_3)))))) && ((! (in_3)) -> (X (((! (out_3)) U (upd)) || (G (! (out_3)))))))))"] }
"""
)
'''
