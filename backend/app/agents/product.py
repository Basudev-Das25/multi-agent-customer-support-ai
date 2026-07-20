from app.agents.base import BaseAgent
from app.schemas.chat import AgentResponse, ChatMessage
from app.services.llm_service import llm_service
from app.services.prompt_service import prompt_service


class ProductAgent(BaseAgent):

    name = "product"

    SYSTEM_PROMPT = """
You are a Product Specialist.

You answer questions about:

- Features
- Pricing
- Comparisons
- Availability

Use only the supplied knowledge base.
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


product_agent = ProductAgent()
