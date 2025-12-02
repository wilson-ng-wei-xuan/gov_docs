from src.evaluator.evaluator import *
import numpy as np
from src.openai.completor import ChatCompletor

class Evaluator:
    def __init__(self):
        self.completor = ChatCompletor()
        self.json_completor = ChatCompletor(use_json = True)
        self.faithfulness = 0
        self.answer_relevance = 0
        self.context_relevance = 0

    async def run_pipeline(self, instruction, answer, context, ground_truth = None):
        claims_list = await claim_breakdown(answer, self.completor)
        # Faithfulness
        f_score, f_score_breakdown = await faithfulness(claims_list, context, self.completor)

        # Answer relevance
        a_score, a_score_breakdown = await answer_relevance(instruction, claims_list, self.completor)
        
        # Context relevance
        c_score, c_score_breakdown = await context_relevance(context, instruction, self.completor)
        
        if ground_truth:
            a_corr, a_corr_breakdown = await answer_correctness(answer, ground_truth, self.json_completor)
        else:
            a_corr = None
            a_corr_breakdown = None
        return f_score, a_score, c_score, a_corr, [f_score_breakdown, a_score_breakdown, c_score_breakdown, a_corr_breakdown]
    
    async def run_multiple(self, data_dict):
        # Initialize lists
        self.f_scores = []
        self.a_scores = []
        self.c_scores = []

        # Run pipeline
        for data in data_dict:
            f_score, a_score, c_score = await self.run_pipeline(data['question'], data['answer'], data['context'])
            self.f_scores.append(f_score)
            self.a_scores.append(a_score)
            self.c_scores.append(c_score)
        self.faithfulness = np.mean(self.f_scores)
        self.answer_relevance = np.mean(self.a_scores)
        self.context_relevance = np.mean(self.c_score)