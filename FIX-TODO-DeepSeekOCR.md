# DeepSeek-OCR vLLM Integration - TODO List

**Status:** Blocked - Deferred pending upstream fixes
**Current Workaround:** Using LLaVA model instead (see docker-compose.yml)
**Reason for Deferral:** DeepSeek-OCR has superior OCR capabilities but requires significant vLLM integration work

## Problems by Complexity (Hardest → Easiest)

### 🔴 HARD: vLLM Model Architecture Implementation
**Estimated Effort:** 40-80 hours
**Complexity:** High - Requires deep vLLM internals knowledge

**Problem:**
DeepSeek-OCR uses MLA (Multi-head Latent Attention) with compressed KV representations, which vLLM doesn't support. vLLM's compatibility checker rejects the model:

```python
# vllm/model_executor/model_loader/utils.py:75
ValueError: DeepseekOCRForCausalLM has no vLLM implementation and the
Transformers implementation is not compatible with vLLM.
```

**Root Causes:**
1. **MLA Attention Architecture**
   - Standard: Uses full key-value cache per head
   - DeepSeek: Compresses KV to shared latent representation
   - Impact: vLLM's KV cache manager incompatible

2. **Custom Vision Integration**
   - Non-standard multimodal input handling
   - Custom position encodings for vision + text
   - vLLM's model loader doesn't handle this pattern

3. **Memory Layout Incompatibility**
   - MLA uses `kv_lora_rank` and compressed projections
   - vLLM expects standard multi-head layout
   - PagedAttention algorithm needs modifications

**Required Changes:**

```python
# New file: vllm/model_executor/models/deepseek_ocr.py

class DeepseekOCRForCausalLM(nn.Module):
    """Native vLLM implementation of DeepSeek-OCR"""

    def __init__(self, config, cache_config, quant_config):
        # 1. Implement MLA attention for vLLM
        self.mla_layers = nn.ModuleList([
            DeepSeekMLALayer(config, layer_idx)
            for layer_idx in range(config.num_hidden_layers)
        ])

        # 2. Integrate vision encoder
        self.vision_encoder = DeepSeekVisionEncoder(config)

        # 3. Custom KV cache handling
        self.kv_cache = CompressedKVCache(cache_config)

    def forward(self, ...):
        # 4. Handle multimodal inputs
        # 5. Custom position encoding
        # 6. MLA attention computation
        pass

# Register with vLLM
# vllm/model_executor/model_loader/utils.py
_KNOWN_VLLM_MODELS = {
    ...
    "DeepseekOCRForCausalLM": ("deepseek_ocr", "DeepseekOCRForCausalLM"),
}
```

**Subtasks:**
- [ ] Implement MLA attention layer compatible with PagedAttention
- [ ] Create compressed KV cache manager
- [ ] Integrate vision encoder with vLLM's input processor
- [ ] Handle multimodal position encodings
- [ ] Write tests for attention correctness
- [ ] Benchmark performance vs standard attention
- [ ] Document memory savings from MLA

**Blockers:**
- Requires understanding of vLLM's PagedAttention kernel
- Need to validate attention output matches transformers
- Performance tuning for GPU efficiency

**Upstream Issues to Watch:**
- vLLM: https://github.com/vllm-project/vllm/issues (check for MLA support requests)
- DeepSeek: May release vLLM-compatible version

---

### 🟡 MEDIUM: Transformers Cache Runtime Patching
**Estimated Effort:** 4-8 hours
**Complexity:** Medium - Requires monkey-patching transformers

**Problem:**
Transformers creates module cache DURING model loading, so we can't pre-patch empty cache:

```python
# transformers/dynamic_module_utils.py:570
def get_class_from_dynamic_module(...):
    final_module = get_cached_module_file(...)  # Downloads NOW
    return get_class_in_module(...)  # Imports broken file
```

**Timing Issue:**
```
1. docker-entrypoint.sh: find /cache -> EMPTY ❌
2. vLLM starts
3. Transformers downloads files to cache
4. Transformers imports broken modeling_deepseekv2.py
5. ImportError: LlamaFlashAttention2
```

**Solution: Monkey-Patch Approach**

```python
# New file: blender-mcp/patch_transformers_loader.py

import transformers.dynamic_module_utils as dmu
from pathlib import Path
import requests

FORK_URL = "https://raw.githubusercontent.com/elasticdotventures/DeepSeek-OCR-fork/main"

def patch_cached_file(file_path: Path):
    """Patch a single cached model file"""
    if file_path.name == "modeling_deepseekv2.py":
        print(f"🔧 Patching {file_path}...")
        response = requests.get(f"{FORK_URL}/modeling_deepseekv2.py")
        response.raise_for_status()
        file_path.write_text(response.text)
        print(f"✅ Patched {file_path}")

def patch_cache_directory(cache_dir: Path):
    """Patch all relevant files in cache directory"""
    for py_file in cache_dir.glob("*.py"):
        if "deepseek" in py_file.name.lower():
            patch_cached_file(py_file)

# Monkey-patch transformers
_original_get_cached = dmu.get_cached_module_file

def patched_get_cached(
    pretrained_model_name_or_path,
    module_file,
    cache_dir=None,
    **kwargs
):
    # Call original to download/cache
    result = _original_get_cached(
        pretrained_model_name_or_path,
        module_file,
        cache_dir,
        **kwargs
    )

    # If it's DeepSeek-OCR, patch the cached directory
    if "deepseek-ocr" in pretrained_model_name_or_path.lower():
        cache_path = Path(result).parent
        patch_cache_directory(cache_path)

    return result

# Apply monkey-patch
dmu.get_cached_module_file = patched_get_cached
print("✅ Transformers loader patched for DeepSeek-OCR compatibility")
```

**Docker Integration:**

```dockerfile
# Dockerfile.vllm
COPY patch_transformers_loader.py /app/
ENV PYTHONPATH=/app:$PYTHONPATH

# docker-entrypoint.sh
#!/bin/bash
# Import patch before starting vLLM
python3 -c "import patch_transformers_loader"
exec python3 -m vllm.entrypoints.openai.api_server "$@"
```

**Subtasks:**
- [ ] Create patch_transformers_loader.py with monkey-patch
- [ ] Update Dockerfile.vllm to copy and configure patch
- [ ] Update docker-entrypoint.sh to import patch
- [ ] Test patch applies correctly during model load
- [ ] Handle network errors downloading from fork
- [ ] Add cache for patched files to avoid repeated downloads

**Risks:**
- Monkey-patching may break with transformers updates
- Network dependency on GitHub for patch files
- Race conditions if multiple models load simultaneously

---

### 🟢 EASY: Transformers API Import Fix
**Estimated Effort:** 1 hour (COMPLETED ✅)
**Complexity:** Low - Simple code replacement

**Problem:**
DeepSeek-OCR imports `LlamaFlashAttention2` which was removed in transformers 4.46+:

```python
# modeling_deepseekv2.py:37
from transformers.models.llama.modeling_llama import (
    LlamaAttention,
    LlamaFlashAttention2  # ❌ Removed in 4.46+
)
```

**Solution: Fork and Update** ✅

Created fork at: https://github.com/elasticdotventures/DeepSeek-OCR-fork

**Changes Made:**

```python
# Fixed import (line 37):
from transformers.models.llama.modeling_llama import LlamaAttention

# Fixed ATTENTION_CLASSES dict (line 1235):
ATTENTION_CLASSES = {
    "eager": DeepseekV2Attention,
    "flash_attention_2": DeepseekV2FlashAttention2,
    "mla_eager": DeepseekV2Attention,
    "mla_flash_attention_2": DeepseekV2FlashAttention2,
    "mha_eager": LlamaAttention,
    "mha_flash_attention_2": LlamaAttention  # ✅ Unified attention
}
```

**Status:** ✅ Complete
- [x] Create GitHub fork
- [x] Update modeling_deepseekv2.py imports
- [x] Update ATTENTION_CLASSES dictionary
- [x] Add TRANSFORMERS_COMPAT.md documentation
- [x] Create patch_deepseek_ocr.sh script
- [x] Test patched files work with transformers 4.51+

**Files:**
- Fork: https://github.com/elasticdotventures/DeepSeek-OCR-fork
- Patch script: `blender-mcp/patch_deepseek_ocr.sh`
- Documentation: `blender-mcp/README.TRANSFORMERS_FIX.md`

---

## Current Status

### What Works ✅
1. Transformers 4.51+ compatibility fix (completed)
2. Patch distribution via GitHub fork
3. Manual patching via `patch_deepseek_ocr.sh`
4. Docker build with patching infrastructure

### What's Blocked 🚫
1. Runtime cache patching (medium complexity)
2. vLLM model architecture support (high complexity)

### Workaround: LLaVA Model 🔄

Using LLaVA instead for now:
- ✅ Native vLLM support
- ✅ Works with transformers 4.51+
- ✅ Vision-language capabilities
- ⚠️ Lower OCR quality than DeepSeek-OCR

```yaml
# docker-compose.yml (current)
command:
  - "--model"
  - "liuhaotian/llava-v1.6-vicuna-7b"  # Using LLaVA instead
```

---

## Decision: Defer to Upstream

**Recommendation:** Use LLaVA now, revisit DeepSeek-OCR later

**Reasoning:**
1. **Time Investment:** 40-80 hours for full vLLM integration
2. **Maintenance Burden:** Need to keep pace with vLLM updates
3. **Upstream Potential:** DeepSeek or vLLM may add official support
4. **Business Value:** LLaVA provides 80% of functionality with 0% custom code

**When to Revisit:**
- [ ] vLLM adds MLA attention support
- [ ] DeepSeek releases vLLM-compatible version
- [ ] Community creates vLLM integration PR
- [ ] OCR quality becomes critical business requirement

**How to Monitor:**
```bash
# Check vLLM for MLA support
gh issue list --repo vllm-project/vllm --search "MLA OR DeepSeek"

# Check DeepSeek for vLLM compatibility
gh issue list --repo deepseek-ai/DeepSeek-OCR --search "vLLM"

# Check transformers for updates
pip list --outdated | grep transformers
```

---

## References

### Code Locations
- **Transformers fix:** `DeepSeek-OCR-fork/modeling_deepseekv2.py`
- **Patch script:** `blender-mcp/patch_deepseek_ocr.sh`
- **Docker entrypoint:** `blender-mcp/docker-entrypoint.sh`
- **Config patches:** Applied by `justfile:install` recipe

### Documentation
- **Technical details:** `DeepSeek-OCR-fork/TRANSFORMERS_COMPAT.md`
- **Integration guide:** `blender-mcp/README.TRANSFORMERS_FIX.md`
- **This file:** `blender-mcp/FIX-TODO-DeepSeekOCR.md`

### External Resources
- DeepSeek-OCR: https://huggingface.co/deepseek-ai/DeepSeek-OCR
- vLLM issues: https://github.com/vllm-project/vllm/issues
- Transformers changelog: https://github.com/huggingface/transformers/releases
- MLA paper: https://arxiv.org/abs/2405.04434

---

**Last Updated:** 2025-10-23
**Status:** Deferred - Using LLaVA workaround
**Next Review:** When upstream adds support or OCR becomes critical
