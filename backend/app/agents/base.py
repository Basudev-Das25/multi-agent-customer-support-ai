from abc import ABC, abstractmethod

from app.schemas.chat import AgentResponse, ChatMessage


class BaseAgent(ABC):
    """
    Base class for all customer support agents.
    """

    name: str = "base"

    @abstractmethod
    async def run(
        self,
        *,
        user_id: str,
        question: str,
        history: list[ChatMessage],
    ) -> AgentResponse:
        """
        Process a user question and return a structured response with sources.
        """
        raise NotImplementedError
