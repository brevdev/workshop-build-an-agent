"""Small data and evaluation checks shared by the customization notebooks."""

import json
import re

import requests

from nemo_gym_resources.langgraph_cli.app import CLIToolCall, normalize_unicode, score_cli_output


def prepare_examples(records):
    """Drop empty/long requests, deduplicate, and reject conflicting labels."""
    examples = {}
    for record in records:
        if not isinstance(record.get("input"), str):
            continue
        text = re.sub(r"<think>.*?</think>", "", record["input"], flags=re.S).strip()
        if not text or len(text) > 300:
            continue
        output = record["output"]
        if isinstance(output, str):
            output = json.loads(output)
        output = CLIToolCall.model_validate(output).model_dump(exclude_none=True)
        key = " ".join(text.casefold().split())
        if key in examples and examples[key]["output"] != output:
            raise ValueError(f"Conflicting labels for request: {text!r}")
        examples.setdefault(key, {"input": text, "output": output})
    if not examples:
        raise ValueError("No usable examples remain. Check the generated input/output columns.")
    return list(examples.values())


def prepare_generated_examples(records):
    """Keep seeded examples only when the request and label preserve their constraints.

    This catches missing literals and invented flags; review meaning separately.
    """
    accepted = []
    for row in records:
        text = normalize_unicode(str(row.get("input", ""))).casefold()
        command = row["command"]
        expected = {"command": command}
        if command == "new":
            expected["template"] = row["template"]
            if row["include_path"]:
                expected["path"] = "./my-agent"
        elif command in ("dev", "up"):
            expected["port"] = int(row["port"])
            flag = "no_browser" if command == "dev" else "watch"
            expected[flag] = bool(row[flag])
            signal = (r"(?:no|without|skip|disable|don't|do not|not).*browser"
                      if flag == "no_browser" else r"watch|reload|code changes")
            if bool(re.search(signal, text)) != expected[flag]:
                continue
        elif command == "build":
            expected["tag"] = row["image_tag"]
        elif command == "dockerfile":
            expected["output_path"] = row["dockerfile_path"]
        literals = [str(value).removeprefix("./").casefold() for key, value in expected.items()
                    if key not in ("command", "no_browser", "watch")]
        if any(value not in text for value in literals):
            continue
        if re.match(r"(?:sure\b|i(?:'ll| will| can)\b|it would be natural)", text):
            continue
        output = row["output"]
        if isinstance(output, str):
            output = json.loads(output)
        if score_cli_output(output, expected)[0] == 1:
            accepted.append(row)
    return prepare_examples(accepted)


def check_split(train_records, val_records):
    """Refuse a before/after comparison with overlapping requests."""
    key = lambda record: " ".join(record["input"].casefold().split())
    overlap = {key(row) for row in train_records} & {key(row) for row in val_records}
    if overlap:
        raise ValueError(f"Train/validation overlap: {len(overlap)} request(s). Deduplicate before splitting.")


def training_token_budget(tokenizer, train_dataset, val_dataset, max_seq_length,
                          min_completion_length=256, prompt_buffer=16):
    """Reserve completion space without silently truncating either data split.

    Measure the rendered chat prompts, including the generation prefix. Refuse
    overlong rows rather than dropping held-out examples from the comparison.
    """
    if min_completion_length <= 0 or max_seq_length <= min_completion_length:
        raise ValueError("MAX_SEQ_LENGTH must leave room for both the prompt and completion.")
    if prompt_buffer < 0:
        raise ValueError("The prompt buffer must be nonnegative.")

    prompt_limit = max_seq_length - min_completion_length
    longest_prompt = 0
    for split_name, dataset in (("Training", train_dataset), ("Held-out", val_dataset)):
        # Transformers 5 defaults to a mapping; count token IDs, not its fields.
        lengths = [len(tokenizer.apply_chat_template(
            row["prompt"], add_generation_prompt=True, tokenize=True, return_dict=False,
        )) for row in dataset]
        if not lengths:
            raise ValueError(f"{split_name} dataset is empty. Check the data-loading cell.")
        oversized = sum(length > prompt_limit for length in lengths)
        if oversized:
            raise ValueError(
                f"{split_name} dataset has {oversized} prompt(s) above the {prompt_limit}-token "
                f"limit after reserving {min_completion_length} completion tokens. "
                "Review/shorten those requests or increase MAX_SEQ_LENGTH if memory allows. "
                "No rows were removed."
            )
        longest_prompt = max(longest_prompt, max(lengths))

    max_prompt_length = min(longest_prompt + prompt_buffer, prompt_limit)
    return max_prompt_length, max_seq_length - max_prompt_length


def _valid_call(parsed):
    """True when the reply contained a JSON object that fits the CLI schema."""
    if not isinstance(parsed, dict):
        return False
    try:
        CLIToolCall.model_validate(parsed)
    except ValueError:  # pydantic's ValidationError is a ValueError
        return False
    return True


def evaluate_cli_model(model, tokenizer, dataset, verify_endpoint, max_new_tokens=256):
    """Greedy, held-out evaluation; never executes a generated shell command.

    Use the same dataset, prompt and generation budget before and after training.
    HTTP/server errors stop the evaluation rather than becoming model scores.
    """
    import torch

    was_training = model.training
    model.eval()
    rows = []
    try:
        for index, example in enumerate(dataset):
            text = tokenizer.apply_chat_template(
                example["prompt"], tokenize=False, add_generation_prompt=True,
            )
            # The chat template already supplies special tokens, as in GRPO.
            inputs = tokenizer(text, return_tensors="pt", add_special_tokens=False).to(model.device)
            with torch.inference_mode():
                output = model.generate(
                    **inputs, max_new_tokens=max_new_tokens, do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                )
            new_tokens = output[0][inputs.input_ids.shape[1]:]
            response = tokenizer.decode(new_tokens, skip_special_tokens=True)
            result = requests.post(verify_endpoint, json={
                "task_id": f"held-out-{index}",
                "task_input": {"input": example["user_input"], "output": example["answer"]},
                "model_response": response,
            }, timeout=30)
            result.raise_for_status()
            score = result.json()
            # Separate formatting failures from wrong answers: a cut-off reply says
            # nothing about whether the model knows the CLI.
            if score["exact_match"]:
                outcome = "exact"
            elif len(new_tokens) >= max_new_tokens:
                outcome = "cut_off"
            elif not _valid_call(score.get("parsed_output")):
                outcome = "invalid_output"
            elif not score.get("command_correct"):
                outcome = "wrong_command"
            else:
                outcome = "wrong_flags"
            rows.append({"input": example["user_input"], "response": response,
                         "reward": score["reward"], "exact_match": score["exact_match"],
                         "outcome": outcome})
    finally:
        model.train(was_training)
    if not rows:
        raise ValueError("The held-out dataset is empty.")
    outcomes = {name: sum(row["outcome"] == name for row in rows)
                for name in ("exact", "wrong_flags", "wrong_command", "invalid_output", "cut_off")}
    return {"count": len(rows), "max_new_tokens": max_new_tokens, "do_sample": False,
            "exact_match_rate": sum(row["exact_match"] for row in rows) / len(rows),
            "mean_reward": sum(row["reward"] for row in rows) / len(rows),
            "outcomes": outcomes, "rows": rows}
