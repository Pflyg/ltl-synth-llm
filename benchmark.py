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
            base_dir, self.name, props["specification"] or self.name + ".tlsf"
        )
        """File path for the specification file"""

        self.implementations = sorted(
            props["implementations"], key=lambda x: next(iter(x["params"].values()))
        )
        """Assures that the implementations are sorted in ascending order. This is only assured if there is only one parameter"""

    def __repr__(self):
        return "<Benchmark '" + self.name + "'>"

    # mode = "self" | "none" | "bosy" | "strix"

    def verify(self, impl: str, overwrite_params: dict = None, timeout=300):
        if overwrite_params == None:
            overwrite_params = self.generate_params
        return verify.verify_code(
            self.specification, impl, overwrite_params=overwrite_params, timeout=timeout
        )

    def verify_implementations(self):
        for impl in self.implementations:
            filename = os.path.join(os.path.dirname(self.specification), impl["file"])
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


def build_prompt(
    bm: Benchmark,
    params=None,
    mode="self",
    template=prompting.DefaultPromptTemplate,
    timeout=120,
    return_raw=False,
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
                }
            )
    return prompt.build_prompt(
        {
            "SPEC": syfco.convert(spec, "ltl", overwrite_params=params),
            "PARAMS": join_params(params),
        }
        if not return_raw
        else prompt
    )


# [bm.verify_implementations() for bm in benchmarks]
