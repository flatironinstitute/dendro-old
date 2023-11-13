from typing import Any, List

class ProcessorBase:
    name: str
    label: str
    description: str
    tags: List[str]
    attributes: dict

    @staticmethod
    def run(
        context: Any
    ):
        raise NotImplementedError()
