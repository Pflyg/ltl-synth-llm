import subprocess
# Note: not all functions of syfco are supported

syfco_path = "syfco"
def _run_command(arguments, input):
    out = subprocess.run(syfco_path + " " + arguments, input = input, shell=True, capture_output = True, text = True)
    if(out.stderr != ""):
        raise Exception(out.stderr)
    return out.stdout
    
def _take_optional_args(overwrite_params : dict =  {}, transformations : list[str] = [], mode = "pretty", quote = "none"):
    return " ".join(
        ["-op " + key + "=" + str(value) for (key, value) in overwrite_params.items()]
          + ["-" + tf for tf in transformations]
        ) + " -m " + mode + " -q " + quote
    
def convert(input : str, format : str = "full", **kwargs):
    """
    Takes a TLSF file as input and converts it to the output format specificied
    Optional Parameters:
      - overwrite_params: dict to overwrite parameters in the TLSF input
      - transformations: array that lists all of the transformations to apply, as described by syfco. Example could be ["s1"]
      - mode: "pretty" [default] minimal parenthesis; "fully" fully parenthesized
      - quote: "none" [default] do not quote identifiers; "double" quote identifiers using "

    """
    args = f'-f {format} {_take_optional_args(**kwargs)} -in'
    return _run_command(args, input).strip()

def inputs(input : str, **kwargs):
    args = f'-f ltl {_take_optional_args(**kwargs)} -in -ins'
    return [s.strip() for s in _run_command(args, input).split(",")]

def outputs(input : str, **kwargs) -> list[str]:
    args = f'-f ltl {_take_optional_args(**kwargs)} -in -outs'
    return [s.strip() for s in _run_command(args, input).split(",")]

def parameters(input : str):
    args = f'-p -in '
    return [s.strip() for s in _run_command(args, input).split(",")]

def title(input : str) -> str:
    args = f'-t -in'
    return _run_command(args, input)[:-1]
def description(input : str) -> str:
    args = f'-d -in'
    return _run_command(args, input)[:-1]

def check(input : str) -> bool:
    args = f'-c -in'
    try:
      return "valid" in _run_command(args, input)    
    except Exception:
      return False
