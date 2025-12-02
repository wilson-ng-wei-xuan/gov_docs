
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt')
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv
load_dotenv()

async def _ragas_cal_similarity(text1, text2, completor):
    emb1 = np.array(await completor.create_embeddings(text1)).reshape(1, -1)
    emb2 = np.array(await completor.create_embeddings(text2)).reshape(1, -1)
    cosine_sim = cosine_similarity(emb1, emb2)[0, 0]
    return cosine_sim

async def _ragas_generate_question(answer,completor):
    prompt = f"""The following is an answer to the question.
    ```answer```: {answer}
    Generate a question for the answer. Output the question without preamble or explanation.
    """
    pred = await completor.open_ai_chat_completion(prompt) 
    return pred

async def ragas_answer_relevance(question, claims_list, completor):
    sim_score = 0
    for claim in claims_list:
        pred_question = await _ragas_generate_question(claim, completor) 
        sim_score += await _ragas_cal_similarity(question, pred_question, completor)  
    return sim_score / len(claims_list)

async def ragas_claim_breakdown(question, answer, completor):
    prompt = f"""Given a question and answer, create one or more statements from each sentence
    in the given answer.
    question: {question}
    answer: {answer}
    """
    claims = await completor.open_ai_chat_completion(prompt) 
    claims_list = claims.split(".")
    claims_list = [claim.strip() for claim in claims_list if len(claim)>3]
    return claims_list

async def ragas_faithfulness(claims_list, context, completor):
    prompt = f"""Consider the given context and following statements, then determine whether they are supported by the information present in the context.
    Provide a brief explanation for each statement before arriving at the verdict (Yes/No). 
    Provide a final verdict for each statement in order at the end in the given format. Do not deviate from the specified format.
    statement: [statement 1]
    ...
    statement: [statement n]

    Context: {context}
    Statements: {'. '.join(claims_list)}
    """

    pred = await completor.open_ai_chat_completion(prompt)
    pred_list = pred.split('\n')
    score = 0
    for explanation in pred_list:
        if "yes" in explanation.lower():
            score+=1
    faithfulness = score / len(claims_list)
    return min(faithfulness, 1.0)

async def ragas_context_relevance(context, question, completor):

    prompt = f"""Please extract relevant sentences from the provided context that can potentially help respond to the following instruction.
    If no relevant sentences are found, or if you believe the instruction cannot be performed from the given context, return the phrase "Insufficient Information".
    While extracting candidate sentences you’re not allowed to make any changes to sentences from given context.
    
    question: ```{question}```

    context: ```{context}```
    """ 
    pred = await completor.open_ai_chat_completion(prompt)
    # Remove sentences containing insufficinet information
    pred_sentences = sent_tokenize(pred)
    final_sentences = [item for item in pred_sentences if "insufficinet information".lower() not in item.lower()]
    context_rel = len(final_sentences) / len(sent_tokenize(context))
    return 1.0 if context_rel > 1.0 else context_rel