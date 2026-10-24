import json
from unittest.mock import patch
import httpx
import pytest
from pydantic import ValidationError
from analyst.config import Settings
from analyst.llm import Plan, generate


def test_plan_rejects_extra_keys():
    with pytest.raises(ValidationError):
        Plan(sql=None, explanation="Need dates", extra="bad")


def test_groq_contract_and_history():
    payload = {"sql": "SELECT COUNT(*) FROM analytics.sales", "explanation": "Count sales."}
    response = httpx.Response(200, request=httpx.Request("POST", "https://example.org"),
                             json={"choices": [{"message": {"content": json.dumps(payload)}}]})
    with patch("analyst.llm.httpx.Client") as client:
        post = client.return_value.__enter__.return_value.post
        post.return_value = response
        result = generate(Settings("unused", "fake-test-key"), "How many sales?",
                          [{"question": "Last month?", "result": {"secret": "never-send"}}])
        assert result.sql == payload["sql"]
        sent = post.call_args.kwargs["json"]
        assert "never-send" not in json.dumps(sent)
        assert sent["response_format"] == {"type": "json_object"}


def test_question_length():
    with pytest.raises(ValueError):
        generate(Settings("unused", "fake"), "x" * 2001)
