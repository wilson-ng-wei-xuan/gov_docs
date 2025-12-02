
def recommend(context_rel, faithfulness, ans_rel, ans_corr=None):
    recommendation = ""
    thresholds = {
            'context_relevance': 0.05,
            'faithfulness': 0.70,
            'answer_relevance': 0.70,
            'answer_correctness': 0.70
        } 
    reply_pass = True
    if context_rel <  thresholds['context_relevance']:
        recommendation += "To improve context relevance, you should include documents relevant to the questions in text format.\n"
        reply_pass = False
    if faithfulness <  thresholds['faithfulness']:
        recommendation += "To improve faithfulness, you should include in your system prompt 'Your output must adhere to the knowledge base'.\n"
        reply_pass = False
    if ans_rel < thresholds['answer_relevance']:
        recommendation += "To improve answer relevance, you should include in your system prompt 'You must directly address the instructions posed'. Kindly check if the questions posed is relevant to your users as well.\n"
        reply_pass = False
    if ans_corr!=None:
        if ans_corr < thresholds['answer_correctness']:
            recommendation += "The answer is either incomplete or contain facts which differ from the ground truth. To improve answer correctness, directly input the correct answer into the documents in text format.\n"
            reply_pass = False
    if reply_pass:
        recommendation = "All metrics are acceptable."
    return recommendation
"""
def recommend(context_rel, faithfulness, ans_rel, general = True):
    thresholds = [
        {
            'metric': 'context_relevance',
            'threshold': 0.05
        },
        {
            'metric': 'faithfulness',
            'threshold': 0.70
        },
        {
            'metric': 'answer_relevance',
            'threshold': 0.70
        },    
    ]
    scores = [context_rel, faithfulness, ans_rel]
    scenario = tuple(score >= threshold['threshold'] for score, threshold in zip(scores, thresholds))
    if general:
        scenario_messages = {
            (True, True, True): "All metrics are acceptable. Please proceed with your AI Bot.",
            (False, True, True): "Context relevance is below threshold. We recommend you to insert answers directly relevant to the qustions into the knowledge base or documents in text format.",
            (True, False, True): "Faithfulness is below threshold. The LLM is answering based on its own knowledge. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details.",
            (True, True, False): "Answer relevance is below threshold. The LLM might have extracted the wrong portion of the context retrieved. We recommend to add instructions related to consistency in your system prompt, for example, 'respond directly to the question or instrcution'.",
            (False, False, True): "Context relevance and faithfulness are both below threshold. We recommend you to insert answers directly relevant to the qustions into the knowledge base or documents in text format. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details.",
            (False, True, False): "Context relevance and answer relevance are both poor. We recommend you to insert answers directly relevant to the qustions into the knowledge base or documents in text format.",
            (True, False, False): "Faithfulness and answer relevance are both poor. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details.",
            (False, False, False): "All metrics are below threshold. It seems like the questions provided are not relevant to the knowledge or documents provided."
        }
    else:
        scenario_messages = {
            (True, True, True): "All metrics are acceptable.",
            (False, True, True): "Context relevance is below threshold. We recommend to add more documents relevant to your questions, or insert relevant knowledge into the text-based knowledge.",
            (True, False, True): "Faithfulness is below threshold. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details.",
            (True, True, False): "Answer relevance is below threshold. The LLM might have extracted the wrong portion of the context retrieved. We recommend to add instructions related to consistency in your system prompt. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details.",
            (False, False, True): "Context relevance and faithfulness are both poor.  The LLM is answering based on its own knowledge. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details. You might need to add relevant knowledge into your documents or text-baed knowledge as well.",
            (False, True, False): "Context relevance and answer relevance are both poor. The LLM is answering based on its own knowledge. Kindly insert relevant knowledge into your documents or text-based knowledge into the AI Bot.",
            (True, False, False): "Faithfulness and answer relevance are both poor. The LLM is hallucinating. We recommend to add guardrails to your system prompt. See the prompt engineering playbook on Launchpad for more details.",
            (False, False, False): "All metrics are below threshold. It seems like the questions are not relevant to the knowledge provided."
        }
    return scenario_messages.get(scenario, "Invalid scenario.")
"""    