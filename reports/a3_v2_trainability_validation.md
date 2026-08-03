# A3_v2 trainability validation

Status: **PASSED**.

The smoke resolved 64 encoder Q/V target modules and exactly 2,621,440 trainable parameters, matching the contract. All trainable parameter names are encoder `q_proj` or `v_proj` LoRA A/B tensors. `base_model_trainable_parameter_names` is empty, so base model weights are frozen. The adapter was written successfully at `runs/A3_v2_resource_smoke/adapter/adapter_model.safetensors`.

Fresh-base initialization was verified by resolved configuration: `initialization_mode=fresh_base`, `parent_adapter=null`, and `parent_weights_loaded=false`. No A2 weights or legacy checkpoint were loaded.
