import asyncio

from app.services.llm_service import llm_service


async def main():

    answer = await llm_service.generate(prompt="Say hello in one sentence.")

    print(answer)


asyncio.run(main())
