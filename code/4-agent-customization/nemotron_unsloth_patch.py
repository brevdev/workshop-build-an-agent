"""
Monkey-patches for the Nemotron-H remote modeling code, applied to the loaded
model class at runtime.

Two distinct bugs are fixed:

1. Forward pass doesn't respect UNSLOTH_RETURN_HIDDEN_STATES. Unsloth's efficient
   GRPO implementation expects the model to return hidden states in the `logits`
   field when that env var is set; Nemotron's custom modeling code ignores it.
   We wrap `forward` to honor the flag.

2. `prepare_inputs_for_generation` crashes on transformers 5.x. The remote code
   was written against transformers 4.x's contract where `cache_position` was
   always non-None at call time. transformers 5.x's new `_prefill()` path can
   pass `cache_position=None`, which causes `TypeError: 'NoneType' object is
   not subscriptable` on `cache_position[-1]`. We wrap the method to
   reconstruct `cache_position` from `past_key_values` when it's missing —
   exactly what transformers 5.x's native NemotronH implementation does via
   its GenerationMixin parent.

Usage:
    from nemotron_unsloth_patch import patch_nemotron_for_unsloth_grpo

    model, tokenizer = FastLanguageModel.from_pretrained(...)
    patch_nemotron_for_unsloth_grpo(model)  # applies both patches above
    model = FastLanguageModel.get_peft_model(model, ...)
"""

import os
from typing import Optional


def patch_nemotron_for_unsloth_grpo(model):
    """
    Patch Nemotron's forward method to respect UNSLOTH_RETURN_HIDDEN_STATES.
    
    Unsloth's efficient GRPO sets UNSLOTH_RETURN_HIDDEN_STATES=1 expecting the model
    to return hidden states in the 'logits' field. Nemotron's custom modeling code
    doesn't support this - this patch adds that support.
    
    Args:
        model: The Nemotron model (can be wrapped in PEFT or not)
        
    Returns:
        None (modifies the model class in-place)
    """
    # Get the actual causal LM model (unwrap PEFT if needed)
    if hasattr(model, 'model'):
        base_model = model.model
        if hasattr(base_model, 'model'):
            causal_lm = base_model.model  # PeftModel -> base_model -> actual model
        else:
            causal_lm = base_model
    else:
        causal_lm = model
    
    # Check if this is a NemotronH model
    model_class_name = causal_lm.__class__.__name__
    if "NemotronH" not in model_class_name:
        print(f"Model is {model_class_name}, not NemotronH - skipping patch")
        return
    
    # Check if already patched
    if getattr(causal_lm.__class__, '_unsloth_patched', False):
        print(f"✓ {model_class_name} already patched for Unsloth GRPO")
        return
    
    # Store original forward
    original_forward = causal_lm.__class__.forward
    
    def patched_forward(
        self,
        input_ids=None,
        inputs_embeds=None,
        position_ids=None,
        cache_params=None,
        labels=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        use_cache=None,
        cache_position=None,
        attention_mask=None,
        **kwargs,
    ):
        """Patched forward that respects UNSLOTH_RETURN_HIDDEN_STATES."""
        # Check if Unsloth wants hidden states instead of logits
        return_hidden_states_as_logits = os.environ.get("UNSLOTH_RETURN_HIDDEN_STATES", "0") == "1"
        
        if not return_hidden_states_as_logits:
            # Normal forward pass
            return original_forward(
                self,
                input_ids=input_ids,
                inputs_embeds=inputs_embeds,
                position_ids=position_ids,
                cache_params=cache_params,
                labels=labels,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
                use_cache=use_cache,
                cache_position=cache_position,
                attention_mask=attention_mask,
                **kwargs
            )
        
        # Unsloth GRPO mode: return hidden states in the logits field
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        
        # Get hidden states from backbone
        nemotron_h_outputs = self.backbone(
            input_ids,
            cache_params=cache_params,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            use_cache=use_cache,
            cache_position=cache_position,
            attention_mask=attention_mask,
        )
        hidden_states = nemotron_h_outputs[0]
        
        # Return hidden states in the logits field (this is what Unsloth GRPO expects)
        from transformers.modeling_outputs import CausalLMOutputWithPast
        return CausalLMOutputWithPast(
            loss=None,
            logits=hidden_states,  # Hidden states, not logits!
            past_key_values=None,
            hidden_states=nemotron_h_outputs.hidden_states if hasattr(nemotron_h_outputs, 'hidden_states') else None,
            attentions=nemotron_h_outputs.attentions if hasattr(nemotron_h_outputs, 'attentions') else None,
        )
    
    # Apply the patch
    causal_lm.__class__.forward = patched_forward
    causal_lm.__class__._unsloth_patched = True
    print(f"✓ Patched {model_class_name}.forward for Unsloth GRPO compatibility")

    # Also patch prepare_inputs_for_generation for transformers 5.x compat.
    _patch_prepare_inputs_for_generation(causal_lm, model_class_name)


def _patch_prepare_inputs_for_generation(causal_lm, model_class_name):
    """
    Null-handle cache_position in NemotronH.prepare_inputs_for_generation.

    The HF Hub remote modeling code for nvidia/NVIDIA-Nemotron-Nano-9B-v2 was
    written against transformers 4.x, where cache_position was guaranteed
    non-None when past_key_values was present. transformers 5.x's _prefill()
    can pass cache_position=None, causing the remote code to crash at
    `cache_position[-1]` with TypeError.

    Mirrors transformers 5.x's native NemotronH implementation, which inherits
    GenerationMixin.prepare_inputs_for_generation — that parent method
    reconstructs cache_position from past_key_values' seq length when missing.
    """
    import torch

    if getattr(causal_lm.__class__, '_cache_position_patched', False):
        print(f"✓ {model_class_name}.prepare_inputs_for_generation already patched")
        return

    original_prep = causal_lm.__class__.prepare_inputs_for_generation

    def patched_prep(self, input_ids, past_key_values=None, attention_mask=None,
                     inputs_embeds=None, cache_position=None, position_ids=None,
                     use_cache=True, **kwargs):
        if cache_position is None and past_key_values is not None:
            past_length = 0
            if hasattr(past_key_values, 'get_seq_length'):
                try:
                    past_length = past_key_values.get_seq_length()
                except Exception:
                    past_length = 0
            elif hasattr(past_key_values, 'seqlen_offset'):
                past_length = past_key_values.seqlen_offset
            cache_position = torch.arange(
                past_length,
                past_length + input_ids.shape[1],
                device=input_ids.device,
            )
        return original_prep(
            self,
            input_ids=input_ids,
            past_key_values=past_key_values,
            attention_mask=attention_mask,
            inputs_embeds=inputs_embeds,
            cache_position=cache_position,
            position_ids=position_ids,
            use_cache=use_cache,
            **kwargs,
        )

    causal_lm.__class__.prepare_inputs_for_generation = patched_prep
    causal_lm.__class__._cache_position_patched = True
    print(f"✓ Patched {model_class_name}.prepare_inputs_for_generation for cache_position=None handling (transformers 5.x compat)")


def verify_patch(model, tokenizer):
    """
    Verify that the monkey-patch is working correctly.
    
    Args:
        model: The patched model
        tokenizer: The tokenizer
        
    Returns:
        bool: True if patch is working, False otherwise
    """
    import torch
    
    os.environ["UNSLOTH_RETURN_HIDDEN_STATES"] = "1"
    
    try:
        test_input = tokenizer("Test", return_tensors="pt").input_ids
        if torch.cuda.is_available():
            test_input = test_input.cuda()
        
        with torch.no_grad():
            test_output = model(test_input)
        
        # Hidden dim for Nemotron-Nano-9B is 4480
        # Vocab size is 131072
        # If patch is working, we should get hidden_dim (4480) not vocab_size
        is_working = test_output.logits.shape[-1] == 4480
        
        if is_working:
            print("✓ Monkey-patch verified: model returns hidden states when UNSLOTH_RETURN_HIDDEN_STATES=1")
        else:
            print(f"✗ WARNING: Patch may not be working. Got shape {test_output.logits.shape}, expected [..., 4480]")
        
        return is_working
    finally:
        os.environ["UNSLOTH_RETURN_HIDDEN_STATES"] = "0"
