# Architecture

~~~
public or synthetic dataset manifest
             |
 normalization -> segmentation condition -> base/adapter candidate
             |                                  |
             +---------- raw and normalized WER/CER ----------+
                                                             |
                                           domain analysis / routing hypothesis
~~~

Every result must identify the corpus revision, split, normalizer, segmentation condition, decoding settings, model revision, and hardware/runtime. The default executable path never downloads a model or dataset.
