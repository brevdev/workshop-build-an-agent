"""Export real LoRA weights without mutating a read-only base checkpoint."""

import hashlib
import json
from pathlib import Path
import sys

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from model_export import save_merged_model


@pytest.mark.parametrize("notebook", [
    "02_grpo_training.ipynb", "answer_key/02_grpo_training.answers.ipynb",
])
def test_save_cell_merges_and_reloads_without_changing_readonly_cache(notebook, tmp_path, monkeypatch):
    import torch
    from peft import LoraConfig, get_peft_model
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from transformers import AutoModelForCausalLM, LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast
    from transformers.core_model_loading import WeightRenaming

    monkeypatch.chdir(tmp_path)
    torch.manual_seed(7)
    base = LlamaForCausalLM(LlamaConfig(
        vocab_size=8, hidden_size=16, intermediate_size=32,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
    ))
    cache = tmp_path / "base-cache"
    base.save_pretrained(cache)
    original = cache / "model.safetensors"
    original.chmod(0o444)
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    model = get_peft_model(AutoModelForCausalLM.from_pretrained(cache), LoraConfig(
        r=2, lora_alpha=4, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM",
    ))
    # Transformers 5 remembers conversions even for trusted remote models.
    # Reversing one during export can rename an embedding the loader needs.
    model.get_base_model()._weight_conversions = [
        WeightRenaming("legacy.embedding", "model.embed_tokens"),
    ]
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            if "lora_B" in name:
                parameter.fill_(0.1)  # Nonzero deltas: a base-only export must fail parity.
    model.eval()
    inputs = torch.tensor([[1, 2, 3]])
    with torch.no_grad():
        expected = model(inputs).logits
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=Tokenizer(WordLevel({"<unk>": 0, "one": 1}, unk_token="<unk>")),
        unk_token="<unk>",
    )
    cells = json.loads((LAB / notebook).read_text())["cells"]
    source = next("".join(cell["source"]) for cell in cells
                  if "from model_export import save_merged_model" in "".join(cell["source"]))
    namespace = {"model": model, "tokenizer": tokenizer}
    exec(source, namespace)
    destination = Path(namespace["OUTPUT_DIR"])
    assert (Path(namespace["ADAPTER_DIR"]) / "adapter_model.safetensors").is_file()
    assert not any("lora_" in key for key in namespace["model"].state_dict())

    # Retry/replacement must also work after an earlier read-only partial export.
    for path in destination.glob("*.safetensors"):
        path.chmod(0o444)
    exec(source, namespace)
    reloaded = AutoModelForCausalLM.from_pretrained(destination).eval()
    with torch.no_grad():
        torch.testing.assert_close(reloaded(inputs).logits, expected, rtol=1e-5, atol=1e-6)
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before
    assert original.stat().st_mode & 0o777 == 0o444


def test_failed_save_keeps_previous_model_and_removes_partial_files(tmp_path):
    destination = tmp_path / "model"
    destination.mkdir()
    (destination / "config.json").write_text("{}")
    (destination / "model.safetensors").write_bytes(b"previous complete model")

    class FailingModel:
        def save_pretrained(self, path, **kwargs):
            path.mkdir()
            (path / "model.safetensors").write_bytes(b"partial")
            raise OSError("disk full")

    with pytest.raises(OSError, match="disk full"):
        save_merged_model(FailingModel(), None, destination)
    assert (destination / "model.safetensors").read_bytes() == b"previous complete model"
    assert list(tmp_path.iterdir()) == [destination]


def test_export_refuses_unrelated_directory_and_symlink(tmp_path):
    unrelated = tmp_path / "user-data"
    unrelated.mkdir()
    (unrelated / "notes.txt").write_text("keep")
    link = tmp_path / "link"
    link.symlink_to(unrelated, target_is_directory=True)
    for path in (unrelated, link):
        with pytest.raises(ValueError):
            save_merged_model(None, None, path)
    assert (unrelated / "notes.txt").read_text() == "keep"
