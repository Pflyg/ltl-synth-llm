import syfco
import subprocess
import os
from aigertoverilog import aiger_to_verilog

strix_path = os.path.abspath("../bin")
custom_env = os.environ.copy()
custom_env["PATH"] = strix_path + ":" + custom_env["PATH"]


def synthesize(
    spec: str,
    target: str = "verilog",
    overwrite_params: dict = {},
    timeout=60,
    module_name="fsm",
) -> str:
    """
    Runs the strix binary with options
    - target: aag (AIGER ASCII), aig (AIGER binary), aiger (alias for aag), hoa, bdd, pg, verilog (experimental)
    - spec: should be in tlsf format
    - overwrite_params: overwrite parameters in tlsf file
    - module_name: only used when target = verilog. Defines the verilog output module name
    """
    verilog_mode = target == "verilog"

    if target == "aiger":
        target = "aag"

    inputs = ",".join(syfco.inputs(spec, overwrite_params=overwrite_params))
    outputs = ",".join(syfco.outputs(spec, overwrite_params=overwrite_params))
    ltl_formula = syfco.convert(
        spec,
        format="ltl",
        mode="fully",
        quote="double",
        overwrite_params=overwrite_params,
    )
    out = subprocess.run(
        [
            "strix",
            "--ins",
            inputs,
            "--outs",
            outputs,
            "-f",
            ltl_formula,
            "-o",
            "aag" if verilog_mode else target,
        ],
        capture_output=True,
        timeout=timeout,
        text=True,
        env=custom_env,
    )

    if out.stderr != "":
        raise Exception(out.stderr)

    # First line is REALIZABLE / UNREALIZABLE
    lines = out.stdout.splitlines()
    if lines[0] != "REALIZABLE":
        raise Exception(lines[0])

    # we have to convert aag to verilog because strix doesn't have direct support
    if not verilog_mode:
        return "\n".join(lines[1:])

    return aiger_to_verilog("\n".join(lines[1:]), module_name)
