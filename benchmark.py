from typing import Any
from utils import read_file, write_file, join_params
import prompting
import json
import os
import verify
import bosy
import strix
import syfco


class BenchmarkEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Benchmark):
            return {
                "name": o.name,
                "params": o.params,
                "generate": o.generate_params,
                "specification": o.specification,
                "implementations": o.implementations,
            }
        return o


class Benchmark:
    def __init__(self, props: dict, base_dir=""):
        self.name = props["name"]
        self.params = props["params"]
        self.generate_params = props["generate"]
        self.specification = os.path.join(
            base_dir, props["specification"] or self.name + ".tlsf"
        )
        """File path for the specification file"""

        self.implementations = sorted(
            props["implementations"], key=lambda x: next(iter(x["params"].values()))
        )
        for impl in self.implementations:
            if "file" in impl:
                impl["file"] = os.path.join(base_dir, impl["file"])
        """Assures that the implementations are sorted in ascending order. This is only assured if there is only one parameter"""

    def __repr__(self):
        return "<Benchmark '" + self.name + "'>"

    @staticmethod
    def load_from_json(json_path: str, base_dir=".") -> list["Benchmark"]:
        return [
            Benchmark(bm, base_dir=base_dir) for bm in json.loads(read_file(json_path))
        ]

    # mode = "self" | "none" | "bosy" | "strix"

    def verify(self, impl: str, overwrite_params: dict = None, timeout=300):
        if overwrite_params == None:
            overwrite_params = self.generate_params
        return verify.verify_code(
            self.specification, impl, overwrite_params=overwrite_params, timeout=timeout
        )

    def verify_implementations(self):
        for impl in self.implementations:
            filename = impl["file"]
            # print(read_file(filename))
            res = verify.verify_file(
                self.specification, filename, overwrite_params=impl["params"]
            )
            if not res == verify.ReturnCode.SUCCESS:
                raise Exception("Could not verify all implementations")


cache_dir = "./cache"


def cache_benchmark_code(bm, impl, func, additional_discriminator=""):
    """
    Synthesizing LTL is expensive
    """
    # make sure the directory exists
    os.makedirs(cache_dir, exist_ok=True)
    filename = f'{bm.name}.{additional_discriminator + "." if additional_discriminator else ""}{".".join([k + "=" + str(v) for (k, v) in impl["params"].items()])}.vl'
    filepath = os.path.join(cache_dir, filename)
    # does file already exist?
    if os.path.isfile(filepath):
        contents = read_file(filepath)
        if contents == "timeout":
            raise TimeoutError()  # if we know that its gonna timeout, there's no sense in building it from scratch
        return contents

    try:
        contents = func()  # calculate
    except TimeoutError:
        write_file(filepath, "timeout")  # save when it timeouts
        raise TimeoutError()
    write_file(filepath, contents)
    return contents


def build_module_definition(spec: str, name: str, params):
    inputs = ["input " + inp for inp in syfco.inputs(spec, overwrite_params=params)]
    outputs = [
        "output reg " + inp for inp in syfco.outputs(spec, overwrite_params=params)
    ]
    joined = ", ".join(inputs + outputs)
    return f"module {name} ({joined})"


def build_prompt(
    bm: Benchmark,
    params=None,
    mode="self",
    template=prompting.DefaultPromptTemplate,
    timeout=120,
    return_raw=False,
    max_examples=100,  # close enough to infinity
):
    """
    - bm: Benchmark object
    - params: overwrite the params to generate
    - mode: which examples to generate. "self" = predefined implementation, "strix" = use strix, "bosy" = use bosy, "none" = no examples
    - template: which prompt template to use to generate the prompt
    - timeout: timeout for generating strix/bosy examples
    - return_raw: if true, return the template object instead
    - max_examples: max examples to generate
    """
    prompt = template()
    spec = read_file(bm.specification)
    if params == None:
        params = bm.generate_params
    if max_examples == 0:
        mode = "none"
    if mode != "none":
        for impl in bm.implementations[-max_examples:]:
            match mode:
                case "self":
                    impl_code = read_file(impl["file"])
                case "bosy":
                    impl_code = cache_benchmark_code(
                        bm=bm,
                        impl=impl,
                        additional_discriminator=mode,
                        func=lambda: bosy.synthesize(
                            spec,
                            overwrite_params=impl["params"],
                            module_name=bm.name,
                            timeout=timeout,
                        ),
                    )
                case "strix":
                    impl_code = cache_benchmark_code(
                        bm=bm,
                        impl=impl,
                        additional_discriminator=mode,
                        func=lambda: strix.synthesize(
                            spec,
                            overwrite_params=impl["params"],
                            module_name=bm.name,
                            timeout=timeout,
                        ),
                    )
                case _:
                    raise Exception("Unsupported mode '" + mode + "'")
            prompt.add_example(
                {
                    "SPEC": syfco.convert(spec, "ltl", overwrite_params=impl["params"]),
                    "IMPL": impl_code,
                    "PARAMS": join_params(impl["params"]),
                    "MODULE_DEF": build_module_definition(
                        spec, bm.name, impl["params"]
                    ),
                }
            )
    return prompt.build_prompt(
        {
            "SPEC": syfco.convert(spec, "ltl", overwrite_params=params),
            "PARAMS": join_params(params),
            "MODULE_DEF": build_module_definition(spec, bm.name, params),
        }
        if not return_raw  # if further changes to the build template object are necessary you can return it directly instead of the prompt
        else prompt
    )


# [bm.verify_implementations() for bm in benchmarks]
