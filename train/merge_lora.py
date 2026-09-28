#!/usr/bin/env python3
"""Merge a LoRA adapter into its base model and save full weights (for stacking DPO on stage A, or serving without LoRA).
  python merge_lora.py --model Qwen/Qwen3-4B-Base --adapter runs/p3_sft/adapter --out runs/p3_sft/merged"""
import argparse, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--adapter", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
m = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16); m = PeftModel.from_pretrained(m, a.adapter).merge_and_unload()
m.save_pretrained(a.out, safe_serialization=True); AutoTokenizer.from_pretrained(a.model).save_pretrained(a.out); print("merged ->", a.out)
