from typing import Iterable
import aiger
from aiger.aig import Node, AndGate, Inverter, Input, LatchIn, ConstFalse, AIG
from natsort import natsorted


def _indent(str: str, char="  ", level=1) -> str:
    if str == "":
        return ""
    ind = level * char
    return "\n".join([ind + str for str in str.split("\n")])


def build_expression(node: Node) -> str:
    match node:
        case AndGate(left=a, right=b):
            return f"({build_expression(a)}) & ({build_expression(b)})"
        case Inverter(input=Inverter(input=i)):
            return build_expression(i)
        case Inverter(input=ConstFalse()):
            return "1"
        case Inverter(input=i):
            if isinstance(i, Input) or isinstance(i, LatchIn):
                return f"!{build_expression(i)}"
            return f"!({build_expression(i)})"
        case ConstFalse():
            return "0"
        case Input(name=s):
            return s
        case LatchIn(name=s):
            return s
        case _:
            raise Exception("Unknown Node type in AIGER graph")


def aiger_to_verilog(aiger_code: str, module_name: str) -> str:
    """
    Takes aiger code and converts it to a verilog module with the same name
    """
    aig: AIG = aiger.parse(aiger_code)

    # Want the symbols to be sorted in a deterministic way. Natsort just
    inputs = natsorted(aig.inputs)
    outputs = natsorted(aig.outputs)
    latches = natsorted(aig.latches)

    # module definition
    module_ports = _indent(
        ",\n".join(
            ["input " + inp for inp in inputs]
            + ["output reg " + out for out in outputs]
        )
    )
    # define state variables
    state_def = "\n".join([f"reg {l};" for l in latches])
    # define initial state
    state_init = _indent(
        "\n".join(
            [f"{l} = {int(aig.latch2init[l])};" for l in latches]
        )  # initial value is either True or False (0 or 1)
    )

    # we only have the state init block if the module actually has a state
    state_init_block = (
        ""
        if len(latches) == 0
        else f"""{state_def}
initial begin
{state_init}
end"""
    )

    # output definitions section
    output_definitions = "\n".join(
        [f"assign {out} = {build_expression(aig.node_map[out])};" for out in outputs]
    )

    # compute the next state from the current state
    state_updates = _indent(
        "\n".join([f"{l} <= {build_expression(aig.latch_map[l])};" for l in latches])
    )

    state_update_block = (
        ""
        if len(latches) == 0
        else f"""
always @(posedge $global_clock) begin
{state_updates}
end"""
    )

    # this is a bit ugly but that's mostly due to the fact that multiline strings cannot be indented
    body = _indent(
        output_definitions
        if len(latches) == 0
        else f"""{state_def}
initial begin
{state_init}
end
{output_definitions}
always @(posedge $global_clock) begin
{state_updates}
end"""
    )

    # putting all parts together
    complete_module = f"""module {module_name} (
{module_ports}
);
{body}
endmodule"""
    return complete_module
