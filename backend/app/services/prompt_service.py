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

        sections = [
            (
                "Use ONLY the information between <context> "
                "and </context> tags below to answer the "
                "user's question."
            ),
            (
                "If the context contains relevant information, "
                "you MUST reference it in your answer."
            ),
            (
                "Never say you cannot find information if "
                "the context contains relevant material."
            ),
            "",
            "<context>",
            context if context.strip() else "No relevant context found.",
            "</context>",
        ]

        if history:
            sections.append("")
            sections.append("### Conversation History")
            for message in history[-10:]:
                sections.append(f"{message.role.capitalize()}: {message.content}")

        sections.extend(
            [
                "",
                "### User Question",
                question,
                "",
                "### Answer (use the context above)",
            ]
        )

        return "\n".join(sections)


prompt_service = PromptService()
