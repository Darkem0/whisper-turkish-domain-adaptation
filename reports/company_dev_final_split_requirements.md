# Company development/final-holdout requirements

Development and final holdout must be separate populations. A `split_group_id` appearing in both is a hard failure. Final holdout is forbidden for model/checkpoint/prompt selection, training, replay, and pseudo-labeling.
