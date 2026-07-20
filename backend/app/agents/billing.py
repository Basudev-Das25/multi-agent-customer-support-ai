from app.agents.base import BaseAgent
from app.schemas.chat import AgentResponse, ChatMessage
from app.services.llm_service import llm_service
from app.services.prompt_service import prompt_service


class BillingAgent(BaseAgent):

    name = "billing"

    SYSTEM_PROMPT = """
You are a Billing Support specialist.

You help with:
- Payments
- Refunds
- Subscriptions
- Invoices

Only answer using the supplied context.
Never invent billing information.
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


billing_agent = BillingAgent()
