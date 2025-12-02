import json
import datetime 
import os
"""
Data Model
[
    {
            "bot_name": bot_name,
            "update_timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "content": [
                {
                    'question': q, 'answer': a, 'context': c, 'faithfulness': i1, 'answer relevance': i2, 'context relevance': i3
                    },...
            ],
            "summary_scores": {
                "summary_faithfulness": summary_faithfulness,
                "summary_context_relevance": summary_context_relevance,
                "summary_answer_relevance": summary_answer_relevance
            }
        }, ...
]
"""


class FileLister:
    def __init__(self, bucket_name, file_name, local = False):
        """
        Record files uploaded list
        args:
            config (dictionary): config yaml
            file_name (str): file path to save to in bucket
           
        """
        self.local = local
        bucket_name = bucket_name.replace('.', '')
        file_name = file_name.split('.json')[0].replace('.', '') +'.json'

        if local:
            self.file_name = f"./data/{bucket_name}/{file_name}"
        else:
            import boto3
            self.s3 = boto3.client('s3')
            # Specify the bucket and file name
            self.bucket_name = bucket_name
            self.file_name = file_name
        

    def read_json(self):
        """Read json from s3 and process"""
        file = {
            "update_timestamp": "0000",
            "content": []
        }
        if self.local:
            if os.path.isfile(self.file_name):
                with open(self.file_name, 'r') as file:
                    file = json.load(file)
            return file

        else:
            try:
                self.s3.head_object(Bucket=self.bucket_name, Key=self.file_name)
                # File exists, so read its content
                response = self.s3.get_object(Bucket=self.bucket_name, Key=self.file_name)
                json_data = response['Body'].read().decode('utf-8')
                file = json.loads(json_data)
                return file
            except:
                # File doesn't exist, so create an empty JSON file
                self.save_json(file)
                print("Empty JSON file created in S3.")
                return file

    def save_json(self, data):
        """Save to s3 function"""
        # Add header to element list
        if self.local:  
            with open(self.file_name, 'w') as file:
                json.dump(data, file, ensure_ascii=False)
        else:
            json_data = json.dumps(data, ensure_ascii=False)
            self.s3.put_object(Body=json_data, Bucket=self.bucket_name, Key=self.file_name)
        return "Success"

    def update_entry(self,
                     bot_name,
                     questions,
                     answers,
                     contexts,
                     ground_truth,
                     f_scores,
                     a_scores,
                     c_scores,
                     a_corrs,
                     summary_faithfulness,
                     summary_answer_relevance,
                     summary_context_relevance,
                     summary_answer_correctness,
                     faith_breakdowns,
                     ans_rel_breakdowns,
                     con_rel_breakdowns,
                     ans_corr_breakdowns
                     ):
        if len(ground_truth) >0:
            qa_context_list = [{'question': q, 'answer': a, 'context': c, 'ground_truth': g, 'faithfulness': i1, 'answer relevance': i2, 'context relevance': i3, 'answer correctness': i4, 'faith_breakdowns': i5, 'ans_rel_breakdowns':i6, 'con_rel_breakdowns': i7, 'answer_correctness_breakdown': i8}
                  for q, a, c, g, i1, i2, i3, i4, i5, i6, i7, i8 in zip(questions, answers, contexts, ground_truth, f_scores, a_scores, c_scores, a_corrs, faith_breakdowns, ans_rel_breakdowns, con_rel_breakdowns, ans_corr_breakdowns )]
            final_dict = {
                "bot_name": bot_name,
                "update_timestamp": (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S.%f'),
                "content": qa_context_list,
                "summary_scores": {
                    "summary_faithfulness": summary_faithfulness,
                    "summary_context_relevance": summary_context_relevance,
                    "summary_answer_relevance": summary_answer_relevance,
                    "summary_answer_correctness": summary_answer_correctness
                }
            }
        else:
            qa_context_list = [{'question': q, 'answer': a, 'context': c, 'ground_truth': 'None', 'faithfulness': i1, 'answer relevance': i2, 'context relevance': i3, 'faith_breakdowns': i4, 'ans_rel_breakdowns':i5, 'con_rel_breakdowns': i6}
                    for q, a, c, i1, i2, i3, i4, i5, i6 in zip(questions, answers, contexts, f_scores, a_scores, c_scores, faith_breakdowns, ans_rel_breakdowns, con_rel_breakdowns )]
            final_dict = {
                "bot_name": bot_name,
                "update_timestamp": (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S.%f'),
                "content": qa_context_list,
                "summary_scores": {
                    "summary_faithfulness": summary_faithfulness,
                    "summary_context_relevance": summary_context_relevance,
                    "summary_answer_relevance": summary_answer_relevance
                }
            }
        return final_dict
