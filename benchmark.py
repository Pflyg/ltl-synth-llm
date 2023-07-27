from typing import Any
from utils import read_file, write_file
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
        return read_file(filepath)
    contents = func()  # calculate
    write_file(filepath, contents)
    return contents


class Benchmark:
    def __init__(self, props: dict, base_dir=""):
        self.name = props["name"]
        self.params = props["params"]
        self.generate_params = props["generate"]
        self.specification = os.path.join(
            base_dir, self.name, props["specification"] or self.name + ".tlsf"
        )
        # Sort implementations by param size
        # I kinda assume that only one parameter is set, but that's all I'm doing in my work anyways
        self.implementations = sorted(
            props["implementations"], key=lambda x: next(iter(x["params"].values()))
        )

    def __repr__(self):
        return "<Benchmark '" + self.name + "'>"

    # mode = "self" | "none" | "bosy" | "strix"

    def verify(self, impl: str, params: dict):
        return verify.verify_code(self.specification, impl, overwrite_params=params)

    def verify_implementations(self):
        for impl in self.implementations:
            filename = os.path.join(os.path.dirname(self.specification), impl["file"])
            # print(read_file(filename))
            res = verify.verify_file(
                self.specification, filename, overwrite_params=impl["params"]
            )
            if not res == verify.ReturnCode.SUCCESS:
                raise Exception("Could not verify all implementations")


def build_prompt(
    bm: Benchmark, params=None, mode="self", template=prompting.DefaultPromptTemplate
):
    prompt = template()
    spec = read_file(bm.specification)
    if params == None:
        params = bm.generate_params

    if mode != "none":
        for impl in bm.implementations:
            match mode:
                case "self":
                    impl_code = read_file(
                        os.path.join(os.path.dirname(bm.specification), impl["file"])
                    )
                case "bosy":
                    impl_code = cache_benchmark_code(
                        bm=bm,
                        impl=impl,
                        additional_discriminator=mode,
                        func=lambda: bosy.synthesize(
                            spec, overwrite_params=impl["params"], module_name=bm.name
                        ),
                    )
                case "strix":
                    impl_code = cache_benchmark_code(
                        bm=bm,
                        impl=impl,
                        additional_discriminator=mode,
                        func=lambda: strix.synthesize(
                            spec, overwrite_params=impl["params"], module_name=bm.name
                        ),
                    )
                case _:
                    raise Exception("Unsupported mode '" + mode + "'")
            prompt.add_example(
                {
                    "SPEC": syfco.convert(spec, "ltl", overwrite_params=impl["params"]),
                    "IMPL": impl_code,
                    "PARAMS": " and ".join(
                        [k + "=" + str(v) for (k, v) in impl["params"].items()]
                    ),
                }
            )
    return prompt.build_prompt(
        {"SPEC": syfco.convert(spec, "ltl", overwrite_params=params)}
    )


# [bm.verify_implementations() for bm in benchmarks]