from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.llm_service import llm_service


@pytest.mark.asyncio
async def test_generate():

    fake_response = Mock()

    fake_response.raise_for_status.return_value = None

    fake_response.json.return_value = {
        "choices": [{"message": {"content": "Hello from Nemotron."}}]
    }

    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=fake_response),
    ):

        answer = await llm_service.generate(
            prompt="Hello",
        )

    assert answer == "Hello from Nemotron."
