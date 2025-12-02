
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt')
import numpy as np
import ast

#from sklearn.metrics.pairwise import cosine_similarity
#from dotenv import load_dotenv
#load_dotenv()

async def claim_breakdown(answer, completor):
    """
    ChangeLOG: 
    1) changed question to instruction.
    2) Added let's think step by step.
    3) Add a checking prompt
    4) Added formatting prompt
    """
    prompt = f"""You are provided with an answer which is used to perform the instruction. The instruction may be a question. Let's think step by step. 
    Break the following answer down into separate independent statements. Output the statement(s), with each claim separated by three semicolons ";;;" without preamble or explanation. 
    Then check if each output statement reflects the meaning in the instruction, and reword it if it does not. Remove all duplicated output statements.
    If a statement is a greeting, output any empty string for that particular statement.
    If there is only one statement, simply output the answer.
    
    answer: ```{answer}```
    """

    claims = await completor.open_ai_chat_completion(prompt) 
    claims_list = claims.split(";;;")
    claims_list = [claim for claim in claims_list if len(claim)>3]
    return claims_list


async def faithfulness(claims_list, context, completor):
    """
    ChangeLOG: 
    1) changed question to instruction.
    2) Added let's think step by step instead of provision of an explantion
    """
    score = 0
    breakdown = []
    claim_length = 0
    for claim in claims_list:
        if len(claim)>3:
            claim_length +=1
            prompt = f"""The following is a ```context``` to an answer and the ```answer``` for the context.
            ```claim```: {claim}

            ```context```: {context}

            Let's think step by step. Determine whether the claim might be supported or inferred by the information in the context. Perform a self-explanation of each statement before arriving at the verdict.
            If the claim is an introduction or conclusion, then the answer is "yes".
            If yes, output "yes". If no, output "no". You must strictly output yes or no only.
            Do not output any preamble or explanation.
            """
            pred = await completor.open_ai_chat_completion(prompt)
            binary_pred = 0 if pred.lower() == "no" else 1
            score += binary_pred
            breakdown.append({'context': context, 'claim': claim, 'score': binary_pred})
        return score / claim_length, breakdown

async def context_relevance(context, instruction, completor):
    """
    ChangeLOG: 
    1) changed question to instruction.
    """
    prompt = f"""Run through sentence by sentence and extract relevant sentences from the provided context that can potentially help respond to the following instruction.
    If no relevant sentences are found, or if you believe the instruction cannot be performed from the given context, return the phrase "Insufficient Information".
    While extracting candidate sentences you’re not allowed to make any changes to sentences from given context.
    
    instruction: ```{instruction}```

    context: ```{context}```
    """ 
    pred = await completor.open_ai_chat_completion(prompt)
    # Remove sentences containing insufficient information
    pred_sentences = sent_tokenize(pred)
    final_sentences = [item for item in pred_sentences if "insufficient information".lower() not in item.lower()]
    context_rel = min(1.0, len(final_sentences) / (len(sent_tokenize(context))+0.0000001))
    breakdown = [
        {
            'context': context,
            'prompt': instruction,
            'relevant_context': pred, 
            'score': context_rel
        }
    ]
    return context_rel, breakdown

async def answer_relevance(instruction, claims_list, completor):
    """
    ChangeLOG: Refactored full metrics calculation.
    """
    score = 0
    breakdown = []
    claim_length = 0
    for claim in claims_list:
        if len(claim)>3:
            claim_length +=1
            prompt = f"""The following is a ```answer``` to an instruction and the ```instruction``` for the answer.
            ```answer```: {claim}
            ```instruction```: {instruction}

            Let's think step by step. Determine if the answer may be relevant to any part of the instruction. The answer is part of a more comphrehensive answer; If it is an introduction, elaboration or conclusion to the instruction, it is considered relevant.
            If yes, output "yes". If no, output "no". Strictly output yes or no. Do not output any preamble or explanation.
            """
            pred = await completor.open_ai_chat_completion(prompt)
            num_pred = 0 if pred == "no" else 1
            score += num_pred
            breakdown.append({'prompt': instruction, 'claim': claim, 'score': num_pred})
    return score/(claim_length+0.000001), breakdown

'''
async def context_relevance(context, instruction, completor):
    context_sentence = sent_tokenize(context)
    score = 0
    for sent in context_sentence:
        prompt = f"""Let's think step by step. Determine if the following evidence is relevant to the instruction.
        ```evidence```: {sent}

        ```instruction```: {instruction}

        If yes, output 1. If no, output 0. Do not output any preamble or explanation.
        """
        pred = await completor.open_ai_chat_completion(prompt)
        score += 0 if pred == "0" else 1
    return score / len(context_sentence)
'''

async def answer_correctness(answer, ground_truth, completor):
    """"""
    prompt = f"""
    Extract statements from predicted answer and ground truth and place it into the respective category. You must stirctly output in json fromat with keys TP, FP, FN (without any premable).
    "TP": you can find a relevant or similar statement (in meaning) in both the answer and the ground truth,
    "FP": you cannot find a relevant or similar statement (in meaning) from the answer in the ground truth,
    "FN": you cannot find a relevant or similar statement (in meaning) from the ground truth in the answer,
    
    Relevance need not be an exact match but you may find similar statements.

    ### PREDICTED ANSWER: {answer}

    ### GROUND TRUTH: {ground_truth}
    """
    prediction = await completor.open_ai_chat_completion(prompt)
    if "```" in prediction:
        prediction = prediction.replace("```", "").replace("json", "").strip()
    prediction = ast.literal_eval(prediction)
    pred_breakdown = prediction
    key_map = [
                "TP",
                "FP",
                "FN",
            ]
    if prediction:
        prediction = [prediction.get(k, np.nan) for k in key_map]
        tp, fp, fn = [
            len(item) if isinstance(item, list) else np.nan for item in prediction
        ]
        if any([np.isnan(i) for i in [tp, fp, fn]]):
            score = np.nan
            print(
                "Invalid prediction format. Expected a list of dictionaries with keys 'TP', 'FP', 'FN'"
            )
        else:
            score = tp / (tp + 0.5 * (fp + fn)) if tp > 0 else 0
    else:
        score = np.nan
    return score, pred_breakdown

async def answer_similarity(answer, ground_truth, completor):
    ans_embeddings = np.array(await completor.create_embeddings(answer))
    ground_truth_embeddings = np.array(await completor.create_embeddings(ground_truth))
    dot_product = np.dot(ans_embeddings, ground_truth_embeddings)
    cosine_similarity = dot_product / ((np.linalg.norm(ans_embeddings)+0.0000001) * np.linalg.norm(ground_truth_embeddings))
    breakdown = {'answer': answer, 'ground_truth': ground_truth}
    return cosine_similarity, breakdown