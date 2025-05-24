from operator_interface.pulse_prompt_logger import prompt_hash


def test_prompt_hash_consistency():
    prompt = "Test prompt"
    config = {"a": 1}
    h1 = prompt_hash(prompt, config)
    h2 = prompt_hash(prompt, config)
    assert h1 == h2
    assert len(h1) == 12


def test_prompt_hash_uniqueness():
    prompt1 = "Prompt 1"
    prompt2 = "Prompt 2"
    config = {"a": 1}
    assert prompt_hash(prompt1, config) != prompt_hash(prompt2, config)
