import httpx

from app.core.config import settings


class LLMService:
    """
    Handles communication with OpenRouter.
    """

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": messages,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        async with httpx.AsyncClient(
            timeout=settings.LLM_TIMEOUT_SECONDS,
        ) as client:

            response = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"OpenRouter request failed: {exc.response.text}"
            ) from exc

        data = response.json()

        choices = data.get("choices", [])

        if not choices:
            raise RuntimeError("OpenRouter returned no completion.")

        message = choices[0].get("message", {})

        content = message.get("content", "").strip()

        if not content:
            raise RuntimeError("Model returned an empty response.")

        return content


llm_service = LLMService()
