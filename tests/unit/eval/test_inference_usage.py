from eval.inference_usage import aggregate_token_usage, usage_from_identification_raw


def test_usage_from_openai_raw_response() -> None:
    raw = {
        "response": {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 25,
                "total_tokens": 125,
            }
        }
    }
    assert usage_from_identification_raw(raw) == {
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "total_tokens": 125,
    }


def test_usage_from_ollama_raw_response() -> None:
    raw = {
        "response": {
            "prompt_eval_count": 50,
            "eval_count": 10,
        }
    }
    assert usage_from_identification_raw(raw) == {
        "prompt_tokens": 50,
        "completion_tokens": 10,
        "total_tokens": 60,
    }


def test_usage_sums_ollama_retry() -> None:
    raw = {
        "response": {"prompt_eval_count": 40, "eval_count": 8},
        "retry": {
            "response": {"prompt_eval_count": 45, "eval_count": 9},
        },
    }
    assert usage_from_identification_raw(raw) == {
        "prompt_tokens": 85,
        "completion_tokens": 17,
        "total_tokens": 102,
    }


def test_aggregate_token_usage_ignores_missing() -> None:
    aggregated = aggregate_token_usage(
        [
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            None,
            {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        ]
    )
    assert aggregated is not None
    assert aggregated.prompt_tokens == 30
    assert aggregated.completion_tokens == 15
    assert aggregated.total_tokens == 45
    assert aggregated.observations_with_usage == 2


def test_aggregate_token_usage_returns_none_when_empty() -> None:
    assert aggregate_token_usage([None, None]) is None
