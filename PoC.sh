#!/bin/bash

models_to_evaluate=("llama2" "mistral")
prompting_techniques=("zero_shot" "one_shot" "chain_of_thought")

for model in "${models_to_evaluate[@]}"; do
    for prompt_tech in "${prompting_techniques[@]}"; do
        python src/wireshairk/__main__.py answer-questions --model "$model" --prompting "$prompt_tech"
        python src/wireshairk/__main__.py evaluate --generated_output "data/evaluation/$model/$prompt_tech"
        python src/wireshairk/__main__.py generate-report --evaluation_input data/evaluation/evaluation_${prompt_tech}_${model}.jsonl
    done
done
