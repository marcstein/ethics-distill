#!/usr/bin/env bash
# Runs ON the pod. Sets up a venv with a torch build matching the pod's driver, plus training and generation deps.
set -e
cd /root && mkdir -p ed && cd ed
command -v uv >/dev/null || (curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1)
export PATH=$HOME/.local/bin:$PATH
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
[ -d .venv ] || uv venv -q --python 3.12 .venv
. .venv/bin/activate
[ "${SKIP_TRAIN_ENV:-0}" = 1 ] || uv pip install -q --torch-backend=auto torch transformers peft accelerate hf_transfer huggingface_hub
[ "${SKIP_TRAIN_ENV:-0}" = 1 ] || python -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
[ -d .venv-vllm ] || uv venv -q --python 3.12 .venv-vllm
# vLLM wheels are built against a specific CUDA; let vLLM choose its own matching torch (no --torch-backend)
VIRTUAL_ENV=$PWD/.venv-vllm uv pip install -q vllm
.venv-vllm/bin/python -c "import vllm, torch; print('vllm', vllm.__version__, 'torch', torch.__version__)" && .venv-vllm/bin/python -c "import vllm._C" 2>/dev/null || { echo "vllm CUDA mismatch, trying cu128 build"; VIRTUAL_ENV=$PWD/.venv-vllm uv pip install -q --torch-backend=cu128 vllm; }
echo BOOTSTRAP_OK
