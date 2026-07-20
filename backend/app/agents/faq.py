from app.agents.base import BaseAgent
from app.schemas.chat import AgentResponse, ChatMessage
from app.services.llm_service import llm_service
from app.services.prompt_service import prompt_service


class FAQAgent(BaseAgent):
    """
    Handles general FAQ and knowledge base questions.
    """

    name = "faq"

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

        if not context.strip():
            return AgentResponse(
                answer=(
                    "I couldn't find information related to your question "
                    "in the knowledge base."
                ),
                agent_name=self.name,
                sources=[],
            )

        prompt = prompt_service.build_prompt(
            question=question,
            context=context,
            history=history,
        )

        answer = await llm_service.generate(
            prompt=prompt,
            system_prompt=prompt_service.SYSTEM_PROMPT,
        )

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            sources=sources,
        )


faq_agent = FAQAgent()
