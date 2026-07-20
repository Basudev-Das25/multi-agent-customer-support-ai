from app.agents.base import BaseAgent
from app.schemas.chat import AgentResponse, ChatMessage
from app.services.llm_service import llm_service
from app.services.prompt_service import prompt_service


class TechnicalAgent(BaseAgent):

    name = "technical"

    SYSTEM_PROMPT = """
You are a Technical Support specialist.

Responsibilities:
- Login problems
- Password reset
- Installation
- Errors
- Bugs

Answer using the provided knowledge base.

If the answer is unavailable,
say you don't have enough information.
"""

    async def run(
        self,
        *,
        user_id: str,
        question: str,
        history: list[ChatMessage],
    ) -> AgentResponse:

        from app.services.retrieval_service import retrieval_service

        context, sources = await retrieval_service.build_response(
            query=question,
        )

        prompt = prompt_service.build_prompt(
            question=question,
            context=context,
            history=history,
        )

        answer = await llm_service.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
        )

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            sources=sources,
        )


technical_agent = TechnicalAgent()
