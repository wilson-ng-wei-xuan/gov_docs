import base64
import os, json
import requests
import boto3

from app.config import (logger, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, STABILITY_API_SECRET, 
                        STABILITY_MODEL_DEFAULT, STABILITY_CFG_SCALE_DEFAULT, STABILITY_STEPS_DEFAULT)
from app.config import boto_config
from app.utils.secret_manager_util import get_json_secret_as_dict

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)
stability_secret = get_json_secret_as_dict(
    STABILITY_API_SECRET,
    endpoint_url=os.getenv("SECRETS_MGR_ENDPOINT_URL"),
    boto_config=boto_config,
)

def stability_generation(prompt, width=512, height=512, samples=1, model=STABILITY_MODEL_DEFAULT, 
                         cfg_scale=STABILITY_CFG_SCALE_DEFAULT, steps=STABILITY_STEPS_DEFAULT, style="enhance"):
    #API reference: https://api.stability.ai/docs

    # Width and height must be in increments of 64 and pass the following requirement
    # For 768 engines:
    # 589,824 <= height * width <= 1,048,576
    # All other engines:
    # 262,144 <= height * width <= 1,048,576

    engine_id = model
    api_host = 'https://api.stability.ai'
    api_key = stability_secret.get("STABILITY_API_KEY")

    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": prompt
                }
            ],
            "cfg_scale": cfg_scale,
            "clip_guidance_preset": "FAST_BLUE",
            "height": height,
            "width": width,
            "samples": samples,
            "steps": steps,
            "style": style
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    # print(json.dumps(data, indent=2))
    # print(data)
    return data

def bedrock_stability_generation(prompt, width=512, height=512, samples=1, model=STABILITY_MODEL_DEFAULT, 
                         cfg_scale=STABILITY_CFG_SCALE_DEFAULT, steps=STABILITY_STEPS_DEFAULT, style="enhance"):
    print(f"{boto3.__version__=}")
    bedrock = boto3.client(service_name='bedrock',region_name='us-east-1',endpoint_url='https://bedrock.us-east-1.amazonaws.com')

    body = json.dumps({"text_prompts":[{"text":prompt}],
                        "cfg_scale": cfg_scale,
                        "clip_guidance_preset": "FAST_BLUE",
                        "height": height,
                        "width": width,
                        "samples": samples,
                        "steps": steps,
                        "style": style}) 
    modelId = 'stability.stable-diffusion-xl'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response = json.loads(response.get('body').read())
    
    return response