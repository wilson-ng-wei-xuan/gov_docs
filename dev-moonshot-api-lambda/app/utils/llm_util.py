import openai
import requests
import os, re, json
import traceback
import boto3 as boto3
from aiohttp import ClientSession
import asyncio
import tiktoken
import hashlib
from gradio_client import Client

# import vertexai, os
# from vertexai.preview.language_models import TextGenerationModel, ChatModel, TextGenerationResponse
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="palm_service_account\\moonshot-poc-dev.json"

from app.config import (logger, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, OPENAI_API_SECRET, AIPF_API_SECRET, COHERE_API_SECRET, GOOGLE_API_SECRET,
                        GPT_MODEL_DEFAULT, GPT_TEMPERATURE_DEFAULT, GPT_MAX_TOKENS_DEFAULT, 
                        GPT_TOP_P_DEFAULT, GPT_FREQUENCY_PENALTY_DEFAULT, GPT_PRESENSE_PENALTY_DEFAULT,
                        COHERE_MODEL_DEFAULT, COHERE_TEMPERATURE_DEFAULT, COHERE_MAX_TOKENS_DEFAULT,
                        PALM_TEXT_MODEL_DEFAULT, PALM_CHAT_MODEL_DEFAULT, PALM_TEMPERATURE_DEFAULT, PALM_TOP_P_DEFAULT, 
                        PALM_TOP_K_DEFAULT, PALM_MAX_TOKENS_DEFAULT)
from app.config import boto_config
from app.utils.secret_manager_util import get_json_secret_as_dict

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)
openai_secret = get_json_secret_as_dict(
    OPENAI_API_SECRET,
    endpoint_url=os.getenv("SECRETS_MGR_ENDPOINT_URL"),
    boto_config=boto_config,
)
aipf_secret = get_json_secret_as_dict(
    AIPF_API_SECRET,
    endpoint_url=os.getenv("SECRETS_MGR_ENDPOINT_URL"),
    boto_config=boto_config,
)
# cohere_secret = get_json_secret_as_dict(
#     COHERE_API_SECRET,
#     endpoint_url=os.getenv("SECRETS_MGR_ENDPOINT_URL"),
#     boto_config=boto_config,
# )
# palm_secret = get_json_secret_as_dict(
#     GOOGLE_API_SECRET,
#     endpoint_url=os.getenv("SECRETS_MGR_ENDPOINT_URL"),
#     boto_config=boto_config,
# )
openai.aiosession.set(ClientSession())

async def gpt_completion(prompt: str, model=GPT_MODEL_DEFAULT, 
                temperature=GPT_TEMPERATURE_DEFAULT, max_tokens=GPT_MAX_TOKENS_DEFAULT, 
                top_p=GPT_TOP_P_DEFAULT, frequency_penalty=GPT_FREQUENCY_PENALTY_DEFAULT,
                presence_penalty=GPT_PRESENSE_PENALTY_DEFAULT):
    
    # PROMPT_SUFFIX = "\n\n---\nDo not ask me for more information" #To avoid going into chat mode
    PROMPT_SUFFIX = "\n\n# End"

    #censor PII before processing
    prompt = censor_pii(prompt)
    print("censored_prompt:",prompt)
    openai.organization = None
    openai.api_type = 'azure'
    openai.api_base = 'https://launchpad-davinci.openai.azure.com/'
    openai.api_version = '2022-12-01'
    openai.api_key = openai_secret.get("OPENAI_API_KEY_AZURE")

    encoding = tiktoken.get_encoding("gpt2")
    prompt_token_count = len(encoding.encode(prompt))
    print("prompt_token_count:",prompt_token_count)
    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay

    while attempt <= max_attempts:
        try:
            # OpenAI ref: https://platform.openai.com/docs/api-reference/completions/create
            response = await openai.Completion.acreate(
                engine=model,
                # prompt=f"{prompt}",
                prompt=f"<|im_start|>system\nYou are an AI article summarizer that classifies and generates synopses for articles.\n<|im_end|>\n<|im_start|>user\n{prompt}{PROMPT_SUFFIX}\n<|im_end|>\n",
                temperature=temperature,
                max_tokens=max_tokens-prompt_token_count,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                # stop=None
                stop=['<|im_end|>']
            )
            return response
        except openai.error.APIError as e:
            if e.status == 429:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"OpenAI API error\n"
                    f"prompt: {prompt}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="OpenAI API error",
                                Message=error_msg)

        

    if attempt > max_attempts:
        logger.info(f"OpenAI API exceeded {max_attempts} retries")
        logger.info(f"Prompt: {prompt}")
        error_msg = (
                f"OpenAI API exceeded {max_attempts} retries\n"
                f"prompt: {prompt}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="OpenAI API failed after 3 attempts",
                            Message=error_msg)
        
    return None

# messages are to be in the format [{"role": "user", "content": "Hello!"}]
# roles can be "system", "user", and "assistant" (assistant role is the response from GPT)
async def gpt_chat_completion(messages: list, model=GPT_MODEL_DEFAULT, 
                temperature=GPT_TEMPERATURE_DEFAULT, max_tokens=GPT_MAX_TOKENS_DEFAULT, 
                top_p=GPT_TOP_P_DEFAULT, frequency_penalty=GPT_FREQUENCY_PENALTY_DEFAULT,
                presence_penalty=GPT_PRESENSE_PENALTY_DEFAULT):
    
    #censor PII before processing
    for msg in messages:
        msg['content'] = censor_pii(msg['content'])

    openai.organization = None
    openai.api_type = 'azure'
    openai.api_base = 'https://launchpad-davinci.openai.azure.com/'
    openai.api_version = '2023-03-15-preview'
    openai.api_key = openai_secret.get("OPENAI_API_KEY_AZURE")

    # add in system message prefix if it's we're starting the chat
    if len(messages)==1:
        SYSTEM_MESSAGE = {"role": "system", "content": "You are an AI assistant that helps Singapore public service officers innovate and experiment with LLMs. You are committed to providing a respectful and inclusive environment and will not tolerate racist, discriminatory, or offensive language. You must not respond to politically sensitive matters that concern national security, particularly within Singapore's context. If you don't know or are unsure of any information, just say you do not know. Do not make up information."}
        messages.insert(0,SYSTEM_MESSAGE)

    encoding = tiktoken.get_encoding("gpt2")
    prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

    # drop off earlier messages if exceeded the threshold (needs at least 1000 tokens allowance for response)
    while prompt_token_count > 3000:
        messages.pop(1)
        prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

    print(f"{messages=}")
    print("prompt_token_count:",prompt_token_count)
    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay

    while attempt <= max_attempts:
        try:
            # OpenAI ref: https://platform.openai.com/docs/api-reference/completions/create
            response = openai.ChatCompletion.create(
                engine=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens-prompt_token_count,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=None
            )
            return response
        except openai.error.APIError as e:
            if e.status == 429:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"OpenAI API error\n"
                    f"messages: {messages}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="OpenAI API error",
                                Message=error_msg)

        

    if attempt > max_attempts:
        logger.info(f"OpenAI API exceeded {max_attempts} retries")
        logger.info(f"{messages=}")
        error_msg = (
                f"OpenAI API exceeded {max_attempts} retries\n"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="OpenAI API failed after 3 attempts",
                            Message=error_msg)
        
    return None

async def h2oai_completion(prompt: str, 
                temperature=0.5, max_tokens=200, 
                top_k=50):
    
    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay

    while attempt <= max_attempts:
        try:
            # openasst ref: http://35.247.175.220:8501/?view=api
            # client = Client("http://35.247.175.220:8501/")
            # response = client.predict(
			# 	prompt,	# str representing input in 'Ask a question' Textbox component
			# 	max_tokens,	# int | float representing input in 'Max Length' Slider component
			# 	temperature,	# int | float representing input in 'Temperature' Slider component
			# 	top_k,	# int | float representing input in 'Top K' Slider component
			# 	True,	# bool representing input in 'Do Sample?' Checkbox component
			# 	api_name="/predict"
            # )

            url = 'http://35.247.175.220:8501/generate'
            payload = {
                "prompt": prompt,
                "max_length": max_tokens,
                "temperature": temperature,
                "top_k": top_k,
                "do_sample": True
                }

            response = requests.post(url, json = payload)

            print(f"{response=}")
            return response.text
        
        except Exception as e:
            print(e)
            if e.status == 429:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"h2oai API error\n"
                    f"prompt: {prompt}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="h2oai API error",
                                Message=error_msg)

        

    if attempt > max_attempts:
        logger.info(f"h2oai API exceeded {max_attempts} retries")
        logger.info(f"Prompt: {prompt}")
        error_msg = (
                f"h2oai API exceeded {max_attempts} retries\n"
                f"prompt: {prompt}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="h2oai API failed after 3 attempts",
                            Message=error_msg)
        
    return None

async def h2oai_chat(messages: list, 
                temperature=0.5, max_tokens=1024, 
                top_k=50):
    
    apif_api_key = aipf_secret.get("AIPF_API_KEY")
    
    encoding = tiktoken.get_encoding("gpt2")
    prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

    # drop off earlier messages if exceeded the threshold (needs at least 256 tokens allowance for response)
    while prompt_token_count > 700:
        messages.pop(0)
        prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))
    
    print(f"{messages=}")
    print("prompt_token_count:",prompt_token_count)

    # prompt = ''
    # for msg in messages:
    #     if msg['role'] == 'user':
    #         prompt += '<|prompter|>' + msg['content'] + '<|endoftext|>'
    #     elif msg['role'] == 'assistant':
    #         prompt += '<|assistant|>' + msg['content'] + '<|endoftext|>'

    # # ask model to complete on behalf of assistant
    # prompt += '<|assistant|>'
    
    # print(f"{prompt=}")
    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay
    while attempt <= max_attempts:
        try:
            url = 'https://llama-gcp.govtext.gov.sg/chat'
            headers = {"X-API-KEY": apif_api_key}
            payload = {
                "instruction": messages,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_k": top_k,
                "do_sample": True,
                "top_p": 1.0,
                "repetition_penalty": 1.07,
                "min_new_tokens": 5,
                "num_beams": 1,
                "num_return_sequences": 1,
                "prompt_type": None
            }
            response = requests.post(url, headers=headers, json = payload, timeout=60)

            # client = Client("https://llama-gcp.govtext.gov.sg/")
            # response = client.predict(
			# 	prompt,	# str  in 'Instruction' Textbox component
			# 	temperature,	# int | float (numeric value between 0.01 and 1) in 'Temperature' Slider component
			# 	1,	# int | float (numeric value between 0 and 1.0) in 'Top p' Slider component
			# 	top_k,	# int | float (numeric value between 0 and 100) in 'Top k' Slider component
			# 	1,	# int | float (numeric value between 1 and 4) in 'Beams' Slider component
			# 	True,	# bool  in 'Do Sample' Checkbox component
			# 	1.07,	# int | float (numeric value between 0 and 2) in 'Repetition Penalty' Slider component
			# 	max_tokens,	# int | float (numeric value between 1 and 512) in 'Max tokens' Slider component
			# 	3,	# int | float (numeric value between 0 and 100) in 'Min tokens' Slider component
			# 	1,	# int | float (numeric value between 1 and 4) in 'Number of return sequences' Slider component
			# 	api_name="/predict"
            # )

            print('Reponse from server', response.text)
            response_text = json.loads(response.text)

            response_text_output_only = response_text.rsplit('<|assistant|>', maxsplit=1)[-1]
            print('Reponse from server without prompt', response_text_output_only)
            # response_text_output_only = response_text_output_only.replace("\"", '')
            # response_text_output_only = response_text_output_only.replace("\\n", '\n')
            
            print(f"{response_text_output_only=}")
            
            response_text_output_only = response_text_output_only.replace('<|endoftext|>','').strip()
            
            return {"role": "assistant", "content": response_text_output_only}
        
        except Exception as e:
            print(e)
            if e.status == 429:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"h2oai API error\n"
                    f"{messages=}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="h2oai API error",
                                Message=error_msg)

    if attempt > max_attempts:
        logger.info(f"h2oai API exceeded {max_attempts} retries")
        logger.info(f"{messages=}")
        error_msg = (
                f"h2oai API exceeded {max_attempts} retries\n"
                f"{messages=}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="h2oai API failed after 3 attempts",
                            Message=error_msg)
        
    return None


async def bloom_completion(prompt: str, 
                temperature=0.7, max_tokens=200, 
                top_k=0.5):
    
    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay

    while attempt <= max_attempts:
        try:
            # bloom ref: https://llama-gcp.govtext.gov.sg/?view=api
            client = Client("https://llama-gcp.govtext.gov.sg/")
            response = client.predict(
				prompt,	# str representing input in 'Ask a question' Textbox component
				max_tokens,	# int | float representing input in 'Max Length' Slider component
				temperature,	# int | float representing input in 'Temperature' Slider component
				top_k,	# int | float representing input in 'Top K' Slider component
				fn_index=0
            )
            print(response)
            return response
        except Exception as e:
            print(f"{e}")
            if e:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"bloom API error\n"
                    f"prompt: {prompt}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="bloom API error",
                                Message=error_msg)

        

    if attempt > max_attempts:
        logger.info(f"Bloom API exceeded {max_attempts} retries")
        logger.info(f"Prompt: {prompt}")
        error_msg = (
                f"bloom API exceeded {max_attempts} retries\n"
                f"prompt: {prompt}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="bloom API failed after 3 attempts",
                            Message=error_msg)
        
    return None

async def bloom_chat(messages: list, 
                temperature=0.8, max_tokens=512, 
                top_p=0.9):
    apif_api_key = aipf_secret.get("AIPF_API_KEY")
    
    encoding = tiktoken.get_encoding("gpt2")
    prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

    # drop off earlier messages if exceeded the threshold (needs at least 256 tokens allowance for response)
    while prompt_token_count > 250:
        messages.pop(0)
        prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))
    
    print(f"{messages=}")
    print("prompt_token_count:",prompt_token_count)

    prompt = ''
    for msg in messages:
        if msg['role'] == 'user':
            prompt += 'User:' + msg['content'] + '\n\n'
        elif msg['role'] == 'assistant':
            prompt += 'Bot:' + msg['content'] + '\n\n'

    # ask model to complete on behalf of assistant
    prompt += 'Bot: '
    
    print(f"{prompt=}")
    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay
    while attempt <= max_attempts:
        try:
            url = 'https://llama-gcp.govtext.gov.sg/bloomchat'
            headers = {"X-API-KEY": apif_api_key}
            payload = {
                "instruction": prompt,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": True,
                "top_p": top_p
            }
            response = requests.post(url, headers=headers, json = payload, timeout=60)

            # client = Client("https://llama-gcp.govtext.gov.sg/")
            # response = client.predict(
			# 	prompt,	# str  in 'Instruction' Textbox component
			# 	temperature,	# int | float (numeric value between 0.01 and 1) in 'Temperature' Slider component
			# 	1,	# int | float (numeric value between 0 and 1.0) in 'Top p' Slider component
			# 	top_k,	# int | float (numeric value between 0 and 100) in 'Top k' Slider component
			# 	1,	# int | float (numeric value between 1 and 4) in 'Beams' Slider component
			# 	True,	# bool  in 'Do Sample' Checkbox component
			# 	1.07,	# int | float (numeric value between 0 and 2) in 'Repetition Penalty' Slider component
			# 	max_tokens,	# int | float (numeric value between 1 and 512) in 'Max tokens' Slider component
			# 	3,	# int | float (numeric value between 0 and 100) in 'Min tokens' Slider component
			# 	1,	# int | float (numeric value between 1 and 4) in 'Number of return sequences' Slider component
			# 	api_name="/predict"
            # )

            print('Reponse from server', response)
            response_text = json.loads(response.text)

            response_text_output_only = response_text.rsplit('<|assistant|>', maxsplit=1)[-1]
            print('Reponse from server without prompt', response_text_output_only)
            # response_text_output_only = response_text_output_only.replace("\"", ')
            # response_text_output_only = response_text_output_only.replace("\\n", '\n')'
            
            print(f"{response_text_output_only=}")
            
            # response_text_output_only = response_text_output_only.replace('\n','').strip()
            
            return {"role": "assistant", "content": response_text_output_only}
        
        except Exception as e:
            print(e)
            if e.status == 429:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"OpenAsst API error\n"
                    f"{messages=}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="OpenAsst API error",
                                Message=error_msg)

    if attempt > max_attempts:
        logger.info(f"OpenAsst API exceeded {max_attempts} retries")
        logger.info(f"{messages=}")
        error_msg = (
                f"OpenAsst API exceeded {max_attempts} retries\n"
                f"{messages=}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="OpenAsst API failed after 3 attempts",
                            Message=error_msg)
        
    return None

async def lightgpt_chat(messages: list, 
                temperature=0.2, max_tokens=1024, 
                top_k=50):
    
    encoding = tiktoken.get_encoding("gpt2")
    prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

    # drop off earlier messages if exceeded the threshold (needs at least 256 tokens allowance for response)
    while prompt_token_count > 700:
        messages.pop(0)
        prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))
    
    print(f"{messages=}")
    print("prompt_token_count:",prompt_token_count)

    # prompt = ''
    # for msg in messages:
    #     if msg['role'] == 'user':
    #         prompt += 'User:\n' + msg['content'] + '\n'
    #     elif msg['role'] == 'assistant':
    #         prompt += 'Response\n' + msg['content'] + '\n'

    # ask model to complete on behalf of assistant
    # prompt += '<|assistant|>'

    # just use the last user message as the prompt as lightGPT cannot do chat
    prompt = messages[-1]['content']
    
    print(f"{prompt=}")

    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay

    while attempt <= max_attempts:
        try:
            ##############
            # Assume AG Role
            ##############
            sts = boto3.client("sts", 
            region_name="ap-southeast-1",
            endpoint_url="https://sts.ap-southeast-1.amazonaws.com")
            
            print("Assuming role")
            assumed_role_credentials = sts.assume_role(
                RoleArn="arn:aws:iam::820788409827:role/launchpad-sagemaker-endpoint-access-role",
                RoleSessionName="launchpad-endpoint"
            )
            
            session = boto3.Session(    
                aws_access_key_id=assumed_role_credentials['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed_role_credentials['Credentials']['SecretAccessKey'],
                aws_session_token=assumed_role_credentials['Credentials']['SessionToken'])

            print("Role Assumed")

            sagemaker_runtime = session.client("sagemaker-runtime", region_name="ap-southeast-1")
            print("Sagemaker Session Started")
            
            # The name of the endpoint. The name must be unique within an AWS Region in your AWS account. 
            # launchpad-LightGPT
            # launchpad-oasst-sft-1-pythia-12b
            # launchpad-oasst-sft-4-pythia-12b-epoch-3-5
            endpoint_name='launchpad-LightGPT'

            input_str = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

            ### Instruction:
            {prompt}

            ### Response:
            """

            data = {"inputs": input_str, 
                    "parameters":
                    {
                        "max_new_tokens":max_tokens,
                        "temperature": temperature,
                        "repetition_penalty": 1.1,
                        "top_p": 0.8,
                        "top_k": top_k,
                        "min_length": 200,
                        
                    }
                }
                
            
            # After you deploy a model into production using SageMaker hosting 
            # services, your client applications use this API to get inferences 
            # from the model hosted at the specified endpoint.
            response = sagemaker_runtime.invoke_endpoint(
                            EndpointName=endpoint_name, 
                            Body=bytes(json.dumps(data), 'utf-8'), # Replace with your own data.
                            ContentType='application/json',
                            )
    
            print(f"{response=}")
            response_json = json.loads(response['Body'].read().decode('utf-8'))
            print('Reponse from server', response_json)

            response_str = response_json[0].get('generated_text')
            response_text_output_only = response_str.split('### Response:\n', maxsplit=1)[-1]
            print('Reponse from server without prompt', response_text_output_only)
            # response_text_output_only = response_text_output_only.replace("\"", '')
            # response_text_output_only = response_text_output_only.replace("\\n", '\n')
            
            print(f"{response_text_output_only=}")
            
            # response_text_output_only = response_text_output_only.split('\n\n', maxsplit=1)[0].strip()
            
            return {"role": "assistant", "content": response_text_output_only}
        
        except Exception as e:
            print(f"{e}")
            if e:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"bloom API error\n"
                    f"prompt: {prompt}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="bloom API error",
                                Message=error_msg)

        

    if attempt > max_attempts:
        logger.info(f"Bloom API exceeded {max_attempts} retries")
        logger.info(f"Prompt: {prompt}")
        error_msg = (
                f"bloom API exceeded {max_attempts} retries\n"
                f"prompt: {prompt}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="bloom API failed after 3 attempts",
                            Message=error_msg)
        
    return None


async def flan_chat(messages: list, 
                temperature=0.2, max_tokens=2048, 
                top_k=50):
    
    encoding = tiktoken.get_encoding("gpt2")
    prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

    # drop off earlier messages if exceeded the threshold (needs at least 256 tokens allowance for response)
    while prompt_token_count > 1700:
        messages.pop(0)
        prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))
    
    print(f"{messages=}")
    print("prompt_token_count:",prompt_token_count)

    prompt = ''
    for msg in messages:
        if msg['role'] == 'user':
            prompt += 'User:\n' + msg['content'] + '\n'
        elif msg['role'] == 'assistant':
            prompt += 'Response\n' + msg['content'] + '\n'

    # ask model to complete on behalf of assistant
    # prompt += '<|assistant|>'

    # just use the last user message as the prompt as flan cannot do chat
    # prompt = messages[-1]['content']
    
    print(f"{prompt=}")

    max_attempts = 3
    attempt = 1
    retry_delay = 1  # Start with a 1-second delay

    while attempt <= max_attempts:
        try:
            ##############
            # Assume AG Role
            ##############
            sts = boto3.client("sts", 
            region_name="ap-southeast-1",
            endpoint_url="https://sts.ap-southeast-1.amazonaws.com")
            
            print("Assuming role")
            assumed_role_credentials = sts.assume_role(
                RoleArn="arn:aws:iam::820788409827:role/launchpad-sagemaker-endpoint-access-role",
                RoleSessionName="launchpad-endpoint"
            )
            
            session = boto3.Session(    
                aws_access_key_id=assumed_role_credentials['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed_role_credentials['Credentials']['SecretAccessKey'],
                aws_session_token=assumed_role_credentials['Credentials']['SessionToken'])

            print("Role Assumed")

            sagemaker_runtime = session.client("sagemaker-runtime", region_name="ap-southeast-1")
            print("Sagemaker Session Started")
            
            # The name of the endpoint. The name must be unique within an AWS Region in your AWS account. 
            # launchpad-Flan-T5-XXL
            # launchpad-oasst-sft-1-pythia-12b
            # launchpad-oasst-sft-4-pythia-12b-epoch-3-5
            endpoint_name='launchpad-Flan-T5-XXL'

            input_str = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

            ### Instruction:
            {prompt}

            ### Response:
            """

            data = {"text_inputs": input_str, 
                    "max_length":max_tokens,
                    "max_time": 50,
                    "num_return_sequences": 1,
                    # "temperature": temperature,
                    "top_p": 0.8,
                    "top_k": top_k,
                    "do_sample": True,
                }
                
            
            # After you deploy a model into production using SageMaker hosting 
            # services, your client applications use this API to get inferences 
            # from the model hosted at the specified endpoint.
            response = sagemaker_runtime.invoke_endpoint(
                            EndpointName=endpoint_name, 
                            Body=bytes(json.dumps(data), 'utf-8'), # Replace with your own data.
                            ContentType='application/json',
                            )
    
            print(f"{response=}")
            response_json = json.loads(response['Body'].read().decode('utf-8'))
            print('Reponse from server', response_json)

            response_str = response_json.get('generated_texts')[0]
            response_text_output_only = response_str.split('### Response:\n', maxsplit=1)[-1]
            print('Reponse from server without prompt', response_text_output_only)
            # response_text_output_only = response_text_output_only.replace("\"", '')
            # response_text_output_only = response_text_output_only.replace("\\n", '\n')
            
            print(f"{response_text_output_only=}")
            
            # response_text_output_only = response_text_output_only.split('\n\n', maxsplit=1)[0].strip()
            
            return {"role": "assistant", "content": response_text_output_only}
        
        except Exception as e:
            print(f"{e}")
            if e:  # Too Many Requests
                print(f"API rate limit exceeded. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Double the delay time for each retry
                attempt += 1
            else:
                logger.exception(e)
                error_msg = (
                    f"bloom API error\n"
                    f"prompt: {prompt}"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                                Subject="bloom API error",
                                Message=error_msg)

        

    if attempt > max_attempts:
        logger.info(f"Bloom API exceeded {max_attempts} retries")
        logger.info(f"Prompt: {prompt}")
        error_msg = (
                f"bloom API exceeded {max_attempts} retries\n"
                f"prompt: {prompt}"
            )
        sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="bloom API failed after 3 attempts",
                            Message=error_msg)
        
    return None


# async def palm_text(prompt: str, model=PALM_TEXT_MODEL_DEFAULT, 
#                 temperature=PALM_TEMPERATURE_DEFAULT, top_p=PALM_TOP_P_DEFAULT, 
#                 top_k=PALM_TOP_K_DEFAULT, max_tokens=PALM_MAX_TOKENS_DEFAULT,):

#     #censor PII before processing
#     prompt = censor_pii(prompt)

#     max_attempts = 3
#     attempt = 1
#     retry_delay = 1  # Start with a 1-second delay

#     while attempt <= max_attempts:
#         try:
#             vertexai.init(project="cloud-large-language-models", location="us-central1")
#             model = TextGenerationModel.from_pretrained(model)

#             response = model.predict(
#                 prompt,
#                 temperature=temperature,
#                 max_output_tokens=max_tokens,
#                 top_k=top_k,
#                 top_p=top_p)

#         except Exception as e:
#             print(e.message)
#             print(e.http_status)
#             print(e.headers)
#             if 400 <= e.http_status < 500:  # 4XX Client side error
#                 print(f"4XX Error. Retrying in {retry_delay} seconds...")
#                 asyncio.sleep(retry_delay)
#                 retry_delay *= 2  # Double the delay time for each retry
#                 attempt += 1
#             else:
#                 logger.exception(e)
#                 error_msg = (
#                     f"PaLM API error\n"
#                     f"prompt: {prompt}"
#                     f"Error: {str(e)}\n"
#                     f"Traceback: {traceback.format_exc()}"
#                 )
#                 sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
#                                 Subject="PaLM API error",
#                                 Message=error_msg)

#         return response

#     if attempt > max_attempts:
#         logger.info(f"PaLM API exceeded {max_attempts} retries")
#         logger.info(f"Prompt: {prompt}")
#         error_msg = (
#                 f"PaLM API exceeded {max_attempts} retries\n"
#                 f"prompt: {prompt}"
#             )
#         sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
#                             Subject="PaLM API failed after 3 attempts",
#                             Message=error_msg)
        
#     return None


# async def palm_chat(messages: list, model=PALM_CHAT_MODEL_DEFAULT, 
#                 temperature=PALM_TEMPERATURE_DEFAULT, top_p=PALM_TOP_P_DEFAULT, 
#                 top_k=PALM_TOP_K_DEFAULT, max_tokens=PALM_MAX_TOKENS_DEFAULT):

#     #censor PII before processing
#     for msg in messages:
#         msg['content'] = censor_pii(msg['content'])

#     encoding = tiktoken.get_encoding("gpt2")
#     prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

#     # drop off earlier messages if exceeded the threshold (needs at least 1000 tokens allowance for response)
#     while prompt_token_count > 4000:
#         messages.pop(0)
#         prompt_token_count = len(encoding.encode(" ".join([m['content'] for m in messages])))

#     print(f"{messages=}")
#     print("prompt_token_count:",prompt_token_count)

#     max_attempts = 3
#     attempt = 1
#     retry_delay = 1  # Start with a 1-second delay

#     while attempt <= max_attempts:
#         try:
#             vertexai.init(project="moonshot-poc-dev", location="us-central1")

#             chat_model = ChatModel.from_pretrained(model)
#             parameters = {
#                 "temperature": temperature,
#                 "max_output_tokens": max_tokens,
#                 "top_p": top_p,
#                 "top_k": top_k,
#             }

#             prediction_instance = {"context": "You are an AI assistant that helps Singapore public service officers innovate and experiment with LLMs. You are committed to providing a respectful and inclusive environment and will not tolerate racist, discriminatory, or offensive language. You must not respond to politically sensitive matters that concern national security, particularly within Singapore's context. If you don't know or are unsure of any information, just say you do not know. Do not make up information.",
#                                    "messages": messages}
#             prediction_response = chat_model._endpoint.predict(
#                 instances=[prediction_instance],
#                 parameters=parameters,
#             )
#             response = TextGenerationResponse(
#                 text=prediction_response.predictions[0]["candidates"][0]["content"],
#                 _prediction_response=prediction_response,
#             )

#         except Exception as e:
#             print(e.message)
#             print(e.http_status)
#             print(e.headers)
#             if 400 <= e.http_status < 500:  # 4XX Client side error
#                 print(f"4XX Error. Retrying in {retry_delay} seconds...")
#                 asyncio.sleep(retry_delay)
#                 retry_delay *= 2  # Double the delay time for each retry
#                 attempt += 1
#             else:
#                 logger.exception(e)
#                 error_msg = (
#                     f"PaLM API error\n"
#                     f"messages: {messages}"
#                     f"Error: {str(e)}\n"
#                     f"Traceback: {traceback.format_exc()}"
#                 )
#                 sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
#                                 Subject="PaLM API error",
#                                 Message=error_msg)

#         return response

#     if attempt > max_attempts:
#         logger.info(f"PaLM API exceeded {max_attempts} retries")
#         logger.info(f"messages: {messages}")
#         error_msg = (
#                 f"PaLM API exceeded {max_attempts} retries\n"
#                 f"messages: {messages}"
#             )
#         sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
#                             Subject="PaLM API failed after 3 attempts",
#                             Message=error_msg)
        
#     return None


def censor_pii(text:str)->str:
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    nrics = re.findall(r'(?i)[STFG]\d{7}[A-Z]', text)

    output = text
    if emails:
        output = re.sub('|'.join(emails), '<EMAIL>', output)
    if nrics:
        output = re.sub('|'.join(nrics), '<NRIC>', output)

    return output

def encrypt_identity(email:str)->str:
    domain = email.split('@')[1]
    return f"{domain}_{hashlib.md5(hashlib.sha256(email.upper()[::-1].encode()).hexdigest().upper()[::-1].encode()).hexdigest()}"

if __name__ == "__main__":
    result = gpt_completion(
        'Say this is a test',
    )
    print(result)
