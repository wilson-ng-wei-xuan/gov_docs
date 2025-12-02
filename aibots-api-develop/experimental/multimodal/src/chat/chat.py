from openai import AzureOpenAI
import os

#from dotenv import load_dotenv
#load_dotenv()

def chat(message, base64Frames = [], transcript = ""):
    client = AzureOpenAI(
        api_key = os.getenv("OPENAI_API_KEY"),  
        api_version = "2023-12-01-preview",
        azure_endpoint = "https://litellm.launchpad.tech.gov.sg"
    )
    
    if len(transcript)>0:
        message = message + f" This is the transcript/speech in the video, or what is known as text or context: {transcript}."

    if len(base64Frames)>0:
        message = message + " These are the images or video frames: "

    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {"type": "text", "text": message},
            *map(lambda x: {"type": "image_url", 
                        "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "low"}}, base64Frames),
        ]}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
    )
    return response.choices[0].message.content