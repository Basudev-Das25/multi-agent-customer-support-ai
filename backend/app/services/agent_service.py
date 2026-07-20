from app.agents.router import router
from app.schemas.chat import AgentResponse, ChatMessage


class AgentService:
    """
    Routes requests to the appropriate specialized agent.
    """

    async def respond(
        self,
        *,
        user_id: str,
        question: str,
        history: list[ChatMessage],
    ) -> AgentResponse:

        agent = router.route(question)

        return await agent.run(
            user_id=user_id,
            question=question,
            history=history,
        )


agent_service = AgentService()
