from abc import ABCMeta, abstractmethod
from vertexai.preview.language_models import InputOutputTextPair


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


class NewPromptTemplate(PromptTemplate):
    _start = "You are an expert in writing correct verilog code, which will fulfill certain formal properties specified in LTL."
    _example = "Here is an example for %PARAMS%. It satisfies the LTL specification %SPEC%:\n```\n%IMPL%\n```"
    _question = "Please write a Verilog module fulfilling the following requirements. Make sure the code is fully synthesizable. Only reply with the correct verilog module matching the LTL specification and nothing else. Specification:\n%SPEC%"


class DefaultPromptTemplate(PromptTemplate):
    _start = "You are an expert in writing correct verilog code, that fulfill certain formal properties specified in LTL."
    _example = "Here is an example for %PARAMS%. It satisfies the LTL specification %SPEC%:\n```\n%IMPL%\n```"
    _question = "Please write a Verilog module for %PARAMS% fulfilling the following specification. Make sure the code is fully synthesizable:\n%SPEC%"


class PromptPALM(DefaultPromptTemplate):
    def add_example(self, replacements: dict = {}):
        pair = InputOutputTextPair(
            interpolate_string(self._question, replacements),
            "```verilog\n" + replacements["IMPL"] + "\n```",
        )
        self.examples.append(pair)

    def build_prompt(self, replacements: dict = {}):
        return (
            interpolate_string(
                self._start + "\n" + self._question,
                replacements,
            ),
            self.examples,
        )


class PromptOpenAI(DefaultPromptTemplate):
    _start = "You are an expert in writing correct verilog code, which will fulfill certain formal properties specified in LTL. Only reply with the correct verilog module matching the specification and nothing else."

    def add_example(self, replacements: dict = {}):
        pair = (
            interpolate_string(self._question, replacements),
            "```verilog\n" + replacements["IMPL"] + "\n```",
        )
        self.examples.append(pair)

    def build_prompt(self, replacements: dict = {}):
        messages = [{"role": "system", "content": self._start}]
        for question, code in self.examples:
            messages += [
                {"role": "user", "content": question},
                {"role": "assistant", "content": code},
            ]
        messages.append(
            {
                "role": "user",
                "content": interpolate_string(self._question, replacements),
            }
        )
        return messages


class ExpertPrompt(DefaultPromptTemplate):
    _start = "Simulate a brilliant computer scientist which is an expert in writing Verilog code such that it satisfies a specification in LTL. At first the expert will be shown some automatically generated examples fro smaller parameter values. Afterwards, he will be asked to write a solution for a bigger specification. It is of upmost importance that the code follows the specification. The prior examples can be used as a basis to start from."
    _example = "Here is a correct example for %PARAMS%. It satisfies the LTL specification %SPEC%:\n%IMPL%"
    _question = "Please write a Verilog module fulfilling the following expectations. Make sure the code is fully synthesizable. Only output the verilog module and nothing else. LTL Specification:\n%SPEC%"


class ModuleDefinitionPromptPALM(PromptPALM):
    _question = """Please write a Verilog module for %PARAMS% using the following module definition as a basis.
```verilog
%MODULE_DEF%
```
The code needs to be fully synthesizable and follow the following LTL specification:
%SPEC%"""


class ModuleDefinitionPromptOpenAI(PromptOpenAI):
    _question = """Please write a Verilog module for %PARAMS% using the following module definition as a basis.
```verilog
%MODULE_DEF%
```
The code needs to be fully synthesizable and follow the following LTL specification:
%SPEC%"""


class PromptOpenAINoSpecification(PromptOpenAI):
    _question = "Please write a Verilog module for %PARAMS% fulfilling the following expectations. Make sure the code is fully synthesizable."


class NoSpecificationPromptPALM(PromptPALM):
    _start = "You are an expert in writing correct verilog code, which will fulfill certain formal properties specified in LTL. You'll be given a parameter value and will generate the corresponding code."
    _example = "Here is an example for %PARAMS%. :\n```\n%IMPL%\n```"
    _question = "Please write a Verilog module for %PARAMS%. Make sure the code is fully synthesizable. Only reply with the correct verilog module matching the specification and nothing else. Do not say you cannot do it and just provide a solution."


class NoSpecificationPromptOpenAI(PromptOpenAI):
    _start = "You are an expert in writing correct verilog code, which will fulfill certain formal properties specified in LTL. You'll be given a parameter value and will generate the corresponding code."
    _example = "Here is an example for %PARAMS%. :\n```\n%IMPL%\n```"
    _question = "Please write a Verilog module for %PARAMS%. Make sure the code is fully synthesizable. Only reply with the correct verilog module matching the specification and nothing else. Do not say you cannot do it and just provide a solution."
