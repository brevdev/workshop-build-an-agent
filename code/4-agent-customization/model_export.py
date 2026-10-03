"""Publish a complete merged checkpoint without modifying cached base weights."""

from pathlib import Path
import os
import shutil
import tempfile

from nemotron_unsloth_patch import patch_nemotron_for_export, save_remote_model_code


def save_merged_model(model, tokenizer, output_dir):
    """Save an already merged model, tokenizer and trusted remote code together.

    Transformers writes fresh shards from the in-memory weights. Unlike the
    affected Unsloth exporter, this does not copy read-only Hub cache shards and
    then try to modify them. A failed save leaves any previous export intact.
    The notebook retains the adapter separately before merging it with PEFT.
    """
    destination = Path(output_dir).expanduser().absolute()
    if destination.is_symlink():
        raise ValueError("Choose a model output directory, not a symlink.")
    if destination.exists():
        if not destination.is_dir():
            raise ValueError("The model output path must be a directory.")
        if any(destination.iterdir()) and not (destination / "config.json").is_file():
            raise ValueError("Use an empty output directory or an existing model export.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Own cleanup explicitly: an interrupted publication must never let an
    # automatic temporary-directory cleanup delete the previous checkpoint.
    work = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    staging = work / "model"
    previous = work / "previous"
    published = False
    try:
        patch_nemotron_for_export(model)
        # Keep the loaded remote model's parameter names. Transformers 5's
        # reverse conversion otherwise renames Nemotron's embeddings and a
        # fresh remote-code loader silently initializes that layer anew.
        model.save_pretrained(
            staging, safe_serialization=True, max_shard_size="5GB",
            save_original_format=False,
        )
        tokenizer.save_pretrained(staging)
        save_remote_model_code(model, staging)
        if not (staging / "config.json").is_file() or not list(staging.glob("model*.safetensors")):
            raise RuntimeError("Export did not produce full model weights; merge the adapter first.")

        try:
            if destination.exists():
                os.replace(destination, previous)
            os.replace(staging, destination)
            published = True
        except BaseException as error:
            # A notebook interrupt can arrive during either rename. Restore
            # only into an absent destination; never overwrite another export.
            if previous.exists() and not destination.exists():
                try:
                    os.replace(previous, destination)
                except BaseException as restore_error:
                    error.add_note(f"Could not restore the previous export: {restore_error}")
            if previous.exists():
                error.add_note(f"Previous export preserved at {previous}; restore it manually if needed.")
            raise
    finally:
        # If rollback fails (or publication was interrupted after the rename),
        # retain the backup and report its path instead of deleting user data.
        if published or not previous.exists():
            shutil.rmtree(work)
