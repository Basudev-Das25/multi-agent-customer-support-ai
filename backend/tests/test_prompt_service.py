from app.services.prompt_service import prompt_service


def test_build_prompt():

    prompt = prompt_service.build_prompt(
        question="What is React Three Fiber?",
        context="React Three Fiber is a React renderer.",
    )

    assert "React Three Fiber is a React renderer." in prompt

    assert "What is React Three Fiber?" in prompt

    assert "Knowledge Base" in prompt
