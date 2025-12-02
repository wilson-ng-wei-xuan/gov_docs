# AI Bots Evaluator

## What is RAGAS?

Visit https://dsaid.atlassian.net/wiki/spaces/PM/pages/69632043/RAGAS

## RAGAS Implementation Details

For each question/answer/context/ground truth pairs, each metric will be calculated. If there is no ground truth, answer correctness will not be generated.

All the metrics will be averaged across all input pairs.

### Faithfulness

1) Utilize GPT to break the answer down into independent parts.

2) Determine how many part of the answer is relevant to the context.

### Context Relevanec

1) Use GPT to determine the parts of the context relevant to the question

2) Count the number of sentences from (1) compared to the number of sentences in the context

### Answer Relevance

1) Utilize GPT to break the answer down into independent parts.

2) Determine how many part of the answer is relevant to the question.

### Answer Correctness

1) Utilize GPT to break the answer down into independent parts.

2) Determine how many part of the answer is relevant to the ground truth.


### Recommendation

If the scores are below arbitrary threshold, then a recommendation will be displayed for the respective recommendation. If multiple metrics are below threshold, the recommendation would be concatanated.

## Important Files

evaluator/evaluator.py #All the evaluator logic

evaluator/ragas_evaluator.py #All the prompt

evaluator/recommendation.py #All the recommendation scripts

### UI and interface considerations

1) What are the metrics to be shown and how to show them

2) How users input instruction and golden answer

3) How users track why something is not as expected

4) Recommended action

### Logging of Prompts

You have to track:

1) When the bots/docs are updated

2) If the question changes

3) Scores for each instruction

Considerations:

1) Cost: Do not require to run the prompts again

2) Consistency: Users see the same score for the same instruction for the same bot