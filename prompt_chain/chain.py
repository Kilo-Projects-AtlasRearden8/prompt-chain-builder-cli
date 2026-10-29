"""Chain orchestration: run prompts sequentially, each output feeding the next."""

from .client import LLMClient, LLMError


class ChainStep:
    """A single step in a prompt chain."""

    def __init__(self, index, prompt, output=None, error=None):
        self.index = index
        self.prompt = prompt
        self.output = output
        self.error = error

    def to_dict(self):
        return {
            "index": self.index,
            "prompt": self.prompt,
            "output": self.output,
            "error": self.error,
        }


class PromptChain:
    """Run a list of prompts where each step's output feeds the next step.

    Step i > 1 receives its own prompt plus the previous step's output as
    appended context, so outputs cascade through the chain.
    """

    SEPARATOR = "\n\n--- Previous output ---\n"

    def __init__(self, client=None):
        self.client = client or LLMClient()
        self.steps = []

    def run(self, prompts, model=None):
        """Run prompts in order. Returns a list of ChainStep dicts."""
        self.steps = []
        previous_output = None
        for index, prompt in enumerate(prompts, start=1):
            full_prompt = prompt
            if previous_output is not None:
                full_prompt = prompt + self.SEPARATOR + previous_output
            try:
                output = self.client.chat(full_prompt, model=model)
                step = ChainStep(index=index, prompt=prompt, output=output)
            except LLMError as exc:
                step = ChainStep(index=index, prompt=prompt, error=str(exc))
                output = None
            self.steps.append(step)
            previous_output = output
        return [step.to_dict() for step in self.steps]
