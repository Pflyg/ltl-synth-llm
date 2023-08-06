import signal
import subprocess
import os
from enum import Enum

from tempfile import NamedTemporaryFile, TemporaryDirectory


path_dirs = ["../../aiger", "../../combine-aiger", "../bin", "../nuxmv/bin"]

path = ":".join([os.path.abspath(p) for p in path_dirs])

custom_env = os.environ.copy()
custom_env["PATH"] = path + ":" + custom_env["PATH"]

script_path = "../verify.sh"

# 2  - invalid input
# 10 - converting to verilog failed
# 11 - failure, model not adhering to spec
# 12 - unknown model checking result
# 13 - could not combine monitor and implementation - usually happens if there are variables present in only one of the two files


class ReturnCode(Enum):
    VERIFICATION_TIMEOUT = -1  # to make error handling easier
    SUCCESS = 0
    UNKNOWN_ERROR = 1
    INVALID_INPUT = 2
    ERROR_CONVERT_TO_VERILOG = 10
    FALSE_RESULT = 11
    UNKNOWN_RESULT = 12
    ERROR_COMBINE_AIGER = 13


def verify_file(
    specification_file: str,
    implementation_file: str,
    overwrite_params: dict = {},
    overwrite_implementation_params=False,
    debug=False,
    timeout=None,
):
    with TemporaryDirectory() as tmpdir:
        if debug:
            tmpdir = os.path.abspath("./.tmp")
        cmd = f"""{os.path.abspath(script_path)} {' '.join(
            ['-p ' + key + '=' + str(value) for (key, value) in overwrite_params.items()]
            + (['-n'] if not overwrite_implementation_params else [])
            + (['-v'] if debug else [])
        )} {os.path.abspath(specification_file)} {os.path.abspath(implementation_file)}"""

        # https://stackoverflow.com/questions/44909625/kill-children-of-python-subprocess-after-subprocess-timeoutexpired-is-thrown
        # https://alexandra-zaharia.github.io/posts/kill-subprocess-and-its-children-on-timeout-python/
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                text=True,
                cwd=tmpdir,
                env=custom_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(
                os.getpgid(proc.pid), signal.SIGTERM
            )  # to make sure nuXmv and co are also killed
            return ReturnCode.VERIFICATION_TIMEOUT
        if debug:
            print(proc.stdout)

        returncode = proc.returncode

    return ReturnCode(proc.returncode)


def verify_code(
    specification_file: str,
    implementation: str,
    overwrite_params: dict = {},
    overwrite_implementation_params=False,
    debug=False,
):
    f = NamedTemporaryFile(suffix=".vl", delete=False, mode="w")
    tmpfile = f.name
    f.write(implementation)
    f.close()
    ret = verify_file(
        specification_file=specification_file,
        implementation_file=tmpfile,
        overwrite_params=overwrite_params,
        overwrite_implementation_params=overwrite_implementation_params,
        debug=debug,
    )
    os.remove(tmpfile)
    return ret


# diprint(verify("detector.tlsf", "impl.vl", overwrite_params={"n": 4}))
