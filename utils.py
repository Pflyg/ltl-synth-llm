import re


# This is a naive way of extracting code, but should work for our purposes
def extract_code_block(str):
    code = re.search(r"```(?:\w+\n)?([\s\S]+?)\n?```", str)
    return None if code == None else code.group(1).strip()


def extract_normalized_verilog_code(str, expected_module_name):
    """
    This makes sure that the extracted code block has the expected module name
    """
    code = extract_code_block(str)
    if code == None:
        return
    mod_name = get_module_name(code)
    if mod_name == None:
        return
    if mod_name == expected_module_name:
        return code
    return rename_module(code, expected_module_name, mod_name)


def read_file(file):
    with open(file) as f:
        return f.read()


def write_file(file, contents):
    with open(file, "w") as f:
        f.write(contents)


def rename_module(code: str, new_name: str, old_name: str = "fsm") -> str:
    """By default, bosy names the generated verilog module "fsm". This module provides the option to rename the module"""
    matches = re.search(
        pattern=r"(.*module\s+)(" + old_name + r")(?:\s*#.*?\))?(\s*\(.*)",
        string=code,
        flags=re.DOTALL,
    )
    return code if matches == None else matches.group(1) + new_name + matches.group(3)


def get_module_name(code: str) -> str:
    """Searches for the module name in verilog code"""
    matches = re.search(
        pattern=r".*module\s+(\w+)(?:\s*#.*?\))?\s*\(.*", string=code, flags=re.DOTALL
    )
    return None if matches == None else matches.group(1)


def join_params(params: dict):
    return " and ".join([k + "=" + str(v) for (k, v) in params.items()])
