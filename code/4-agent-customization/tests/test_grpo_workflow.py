"""Regression checks for the notebook's budget → configure → train → compare flow."""

import ast
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
import nemotron_unsloth_patch
import training_support


class LengthTokenizer:
    """Represent each fully rendered chat prompt by its token count."""

    def apply_chat_template(self, prompt, *, add_generation_prompt, tokenize, return_dict=True):
        assert add_generation_prompt is True
        assert tokenize is True
        if return_dict:
            return {"input_ids": list(range(prompt)), "attention_mask": [1] * prompt}
        return range(prompt)


def rows(*lengths):
    return [{"prompt": length} for length in lengths]


@pytest.mark.parametrize("train_length,val_length,expected", [
    (100, 200, (216, 808)),  # Held-out prompts can be longer than training prompts.
    (760, 100, (768, 256)),  # Clip the buffer, never the prompt or completion reserve.
    (100, 768, (768, 256)),
])
def test_budget_covers_both_splits_within_total_limit(train_length, val_length, expected):
    train, val = rows(train_length), rows(val_length)
    assert training_support.training_token_budget(LengthTokenizer(), train, val, 1024) == expected
    assert train == rows(train_length)
    assert val == rows(val_length)
    assert sum(expected) == 1024


@pytest.mark.parametrize("train,val,message", [
    ([], rows(100), "Training dataset is empty"),
    (rows(100), [], "Held-out dataset is empty"),
    (rows(769), rows(100), "Training dataset has 1 prompt"),
    (rows(100), rows(769), "Held-out dataset has 1 prompt"),
])
def test_invalid_split_stops_instead_of_silently_dropping_rows(train, val, message):
    original = json.dumps([train, val])
    with pytest.raises(ValueError, match=message):
        training_support.training_token_budget(LengthTokenizer(), train, val, 1024)
    assert json.dumps([train, val]) == original


@pytest.mark.parametrize("settings", [
    {"max_seq_length": 256},
    {"max_seq_length": 1024, "min_completion_length": 0},
    {"max_seq_length": 1024, "prompt_buffer": -1},
])
def test_invalid_budget_settings_are_actionable(settings):
    with pytest.raises(ValueError):
        training_support.training_token_budget(LengthTokenizer(), rows(100), rows(100), **settings)


def test_evaluation_keeps_template_tokens_and_restores_training_mode(monkeypatch):
    torch = pytest.importorskip("torch")
    from fastapi.testclient import TestClient
    from nemo_gym_resources.langgraph_cli.app import app

    client = TestClient(app)
    monkeypatch.setattr(training_support.requests, "post",
                        lambda url, json, timeout: client.post("/verify", json=json))

    class Inputs(dict):
        @property
        def input_ids(self):
            return self["input_ids"]

        def to(self, device):
            return self

    class Tokenizer:
        pad_token_id = 0

        def apply_chat_template(self, prompt, *, tokenize, add_generation_prompt):
            assert not tokenize and add_generation_prompt
            return "rendered chat with special tokens"

        def __call__(self, text, *, return_tensors, add_special_tokens=True):
            assert not add_special_tokens  # Match the tokens measured for GRPO.
            return Inputs(input_ids=torch.tensor([[1, 2]]))

        def decode(self, token_ids, *, skip_special_tokens):
            assert token_ids.tolist() == [3] and skip_special_tokens
            return '{"command":"dev","port":8080}'

    class Model:
        training = True
        device = "cpu"

        def eval(self):
            self.training = False

        def train(self, mode):
            self.training = mode

        def generate(self, input_ids, *, max_new_tokens, do_sample, pad_token_id):
            assert not self.training and not do_sample and max_new_tokens == 256
            return torch.cat((input_ids, torch.tensor([[3]])), dim=1)

    model = Model()
    result = training_support.evaluate_cli_model(model, Tokenizer(), [{
        "prompt": [], "user_input": "Start port8080", "answer": {"command": "dev", "port": 8080},
    }], "http://verifier.test/verify")
    assert result["count"] == 1 and result["exact_match_rate"] == 1
    assert result["mean_reward"] == 1 and model.training


class CompleteTrainingExercises(ast.NodeTransformer):
    """Supply only the choices explicitly requested in the two exercise prompts."""

    choices = {
        "GRPOConfig": {"num_generations": "4", "learning_rate": "5e-5", "max_steps": "50"},
        "GRPOTrainer": {"model": "model", "processing_class": "tokenizer",
                        "reward_funcs": "[reward_fn]", "args": "training_args",
                        "train_dataset": "train_dataset"},
    }

    def visit_Call(self, node):
        self.generic_visit(node)
        choices = self.choices.get(getattr(node.func, "id", None), {})
        for keyword in node.keywords:
            if isinstance(keyword.value, ast.Constant) and keyword.value.value is Ellipsis:
                keyword.value = ast.parse(choices[keyword.arg], mode="eval").body
        return node


@pytest.mark.parametrize("notebook", [
    "02_grpo_training.ipynb", "answer_key/02_grpo_training.answers.ipynb",
])
def test_notebook_trains_once_after_configuration_and_compares_same_holdout(
        notebook, monkeypatch, tmp_path):
    """Execute the real cells with small stand-ins; this is not a GPU training test."""
    monkeypatch.chdir(tmp_path)
    events = []
    train, val = rows(100), rows(200)
    tokenizer = LengthTokenizer()
    reward_fn = lambda **kwargs: [1.0]

    class Model:
        adapters_disabled = False
        trained = False

        @contextmanager
        def disable_adapter(self):
            self.adapters_disabled = True
            try:
                yield
            finally:
                self.adapters_disabled = False

    model = Model()

    def config(**kwargs):
        events.append("configure")
        assert kwargs["max_prompt_length"] == 216
        # Training and evaluation share one short budget for JSON answers.
        assert kwargs["max_completion_length"] == 128
        assert (kwargs["num_generations"], kwargs["learning_rate"], kwargs["max_steps"]) == (4, 5e-5, 50)
        # TRL counts completions: 4 per micro-batch x 4 accumulation steps = 4 prompts x 4 generations.
        assert kwargs["per_device_train_batch_size"] * kwargs["gradient_accumulation_steps"] == 4 * kwargs["num_generations"]
        return SimpleNamespace(**kwargs)

    class Trainer:
        state = SimpleNamespace(log_history=[
            {"step": step, "reward": 0.5, "reward_std": 0.2, "frac_reward_zero_std": 0.5,
             "completions/mean_length": 20.0} for step in range(1, 13)] + [{"train_runtime": 1.0}])

        def __init__(self, **kwargs):
            events.append("construct")
            assert kwargs == {"model": model, "processing_class": tokenizer,
                              "reward_funcs": [reward_fn], "args": ns["training_args"],
                              "train_dataset": train}

        def train(self):
            events.append("train")
            assert not model.adapters_disabled
            assert not model.trained
            assert events[-2] == "baseline"
            model.trained = True

    def evaluate(actual_model, actual_tokenizer, dataset, endpoint, max_new_tokens):
        assert actual_model is model and actual_tokenizer is tokenizer
        assert dataset is val and endpoint == "http://verifier.test/verify"
        assert max_new_tokens == 128
        if model.adapters_disabled:
            assert not model.trained
            events.append("baseline")
        else:
            assert model.trained
            events.append("trained")
        return {"exact_match_rate": 0.0, "count": len(dataset), "max_new_tokens": max_new_tokens,
                "outcomes": {"exact": 0}, "rows": [{"exact_match": False}]}

    monkeypatch.setattr(training_support, "evaluate_cli_model", evaluate)
    monkeypatch.setattr(nemotron_unsloth_patch, "verify_patch", lambda *args: events.append("verify"))
    ns = {"model": model, "tokenizer": tokenizer, "train_dataset": train, "val_dataset": val,
          "MAX_SEQ_LENGTH": 1024, "VERIFY_ENDPOINT": "http://verifier.test/verify",
          "GRPOConfig": config, "GRPOTrainer": Trainer, "reward_fn": reward_fn, "json": json,
          "MODEL_NAME": "base-model", "MODEL_REVISION": "pinned-revision"}
    cells = json.loads((LAB / notebook).read_text())["cells"]
    in_training_section = False
    for cell in cells:
        source = "".join(cell["source"])
        if source.startswith("## Step 6:"):
            in_training_section = True
        if source.startswith("## Step 8:"):
            break
        if in_training_section and cell["cell_type"] == "code":
            tree = CompleteTrainingExercises().visit(ast.parse(source))
            exec(compile(ast.fix_missing_locations(tree), notebook, "exec"), ns)

    assert events == ["verify", "configure", "construct", "baseline", "train", "trained"]
    comparison = json.loads((tmp_path / "outputs/grpo_langgraph_cli/held_out_comparison.json").read_text())
    assert comparison["base_revision"] == "pinned-revision"
    assert comparison["baseline"] == comparison["trained"]  # Zero improvement remains a valid result.
    assert (comparison["improved"], comparison["regressed"]) == (0, 0)
    assert list(ns["curve"].index) == ["steps 1-10", "steps 11-12"]
    assert train == rows(100) and val == rows(200)
