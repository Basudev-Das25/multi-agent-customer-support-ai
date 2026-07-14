from app.schemas.chat import ChatMessage


class PromptService:
    """
    Builds prompts for the language model.
    """

    SYSTEM_PROMPT = """You are an AI Customer Support Assistant.

Your job is to answer ONLY using the provided knowledge base.

Rules:

1. Answer using the supplied context.
2. If the answer cannot be found, say:
   "I couldn't find that information in the knowledge base."
3. Never invent information.
4. Be concise and professional.
5. Use bullet points when appropriate.
6. If code exists in the context, preserve formatting.
"""

    def build_prompt(
        self,
        *,
        question: str,
        context: str,
        history: list[ChatMessage] | None = None,
    ) -> str:
        """
        Build the complete prompt sent to the LLM.
        """

        prompt = [
            self.SYSTEM_PROMPT,
            "",
            "### Knowledge Base",
            context or "No relevant context found.",
        ]

        if history:
            prompt.append("")
            prompt.append("### Conversation History")

            for message in history[-10:]:
                prompt.append(f"{message.role.capitalize()}: {message.content}")

        prompt.extend(
            [
                "",
                "### User Question",
                question,
                "",
                "### Assistant",
            ]
        )

        return "\n".join(prompt)


prompt_service = PromptService()
