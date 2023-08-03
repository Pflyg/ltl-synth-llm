from abc import ABCMeta, abstractmethod


def interpolate_string(string: str, replacements: dict) -> str:
    for key, val in replacements.items():
        string = string.replace("%" + key + "%", val)
    return string


class PromptTemplate(metaclass=ABCMeta):
    def __init__(self) -> None:
        self.examples = []

    def add_example(self, replacements: dict = {}):
        self.examples.append(interpolate_string(self._example, replacements))

    def build_prompt(self, replacements: dict = {}):
        return interpolate_string(
            self._start + "\n" + "\n".join(self.examples) + "\n" + self._question,
            replacements,
        )

    @property
    @abstractmethod
    def _start():
        pass

    @property
    @abstractmethod
    def _example():
        pass

    @property
    @abstractmethod
    def _question():
        pass


class DefaultPromptTemplate(PromptTemplate):
    _start = "You are an expert in writing correct verilog code, that fulfill certain formal properties specified in LTL."
    _example = "Here is an example for %PARAMS%. It satisfies the LTL specification %SPEC%:\n```\n%IMPL%\n```"
    _question = "Please write a Verilog module fulfilling the following expectations. Make sure the code is fully synthesizable.:\n%SPEC%"
