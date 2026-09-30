"""Additive patches so train_lora.py and eval/gen.py accept non-Qwen bases (Gemma 4, Mistral 3) shipped as multimodal wrappers."""
import re
p = "train/train_lora.py"; s = open(p).read()
if "--end eos" not in s:
    s = s.replace('a = ap.parse_args()\ntok = AutoTokenizer.from_pretrained(a.model); tok.pad_token = tok.pad_token or "<|endoftext|>"',
                  'a = ap.parse_args()\ntok = AutoTokenizer.from_pretrained(a.model); tok.pad_token = tok.pad_token or tok.eos_token or "<|endoftext|>"\n'
                  'if a.end == "eos": a.end = tok.eos_token   # --end eos: use the base model\'s own end-of-sequence token (Gemma <eos>, Mistral </s>, Qwen <|endoftext|>)\n'
                  'print("end token:", repr(a.end), tok.convert_tokens_to_ids(a.end), flush=True)')
    s = s.replace('model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()',
                  'try: model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()\n'
                  'except Exception as e:   # multimodal wrappers (Gemma4/Mistral3 ForConditionalGeneration): load the full model, train the language model\'s projections\n'
                  '    print("AutoModelForCausalLM failed (%s); loading AutoModelForImageTextToText" % str(e)[:120], flush=True)\n'
                  '    from transformers import AutoModelForImageTextToText\n'
                  '    model = AutoModelForImageTextToText.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()')
    open(p, "w").write(s); print("patched", p)
else: print("already patched", p)
p = "eval/gen.py"; s = open(p).read()
if "eos_token_id" not in s:
    s = s.replace('llm = LLM(model=a.model, dtype="bfloat16", max_model_len=8192, gpu_memory_utilization=0.88, seed=0,',
                  'from transformers import AutoTokenizer as _AT; _tok = _AT.from_pretrained(a.model); _eos = [i for i in [_tok.eos_token_id] if i is not None]\n'
                  'llm = LLM(model=a.model, dtype="bfloat16", max_model_len=8192, gpu_memory_utilization=0.88, seed=0, limit_mm_per_prompt={"image": 0},')
    s = s.replace('stop=["<|im_end|>", "<|endoftext|>"], repetition_penalty=1.03)', 'stop=["<|im_end|>", "<|endoftext|>", "\\n<|im_start|>"], stop_token_ids=_eos, repetition_penalty=1.03)')
    open(p, "w").write(s); print("patched", p)
else: print("already patched", p)
