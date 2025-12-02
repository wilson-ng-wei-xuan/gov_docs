import base64
import json
import random
from typing import Optional

from fastapi import APIRouter, Security, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, AnyHttpUrl
from fastapi.responses import RedirectResponse

from app import config
from app.models.inference.inference_model import GptInferenceModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import dynamodb, TABLE_MOONSHOT_LLM, GPT_MODEL_DEFAULT, GPT_TEMPERATURE_DEFAULT, GPT_MAX_TOKENS_DEFAULT, GPT_TOP_P_DEFAULT, GPT_FREQUENCY_PENALTY_DEFAULT, GPT_PRESENSE_PENALTY_DEFAULT
import logging

from app.config import logger

router = APIRouter()
security_http_bearer = HTTPBearer()

model_gpt_inference = GptInferenceModel(dynamodb, TABLE_MOONSHOT_LLM)

class GptInferenceType(BaseModel):
    text: str
    cliffhanger: Optional[bool] = False

    class Config:
        schema_extra = {
            "example": {
                "text": """If you've ever looked up a restaurant on Google Maps, you may get an idea of the menu and the decor. 

                        see also
                        Google Docs' voice-to-text feature is getting major upgrades. Here's how to use it
                        How to clear Google search cache on Android (and why you should)
                        How to use tab groups in Google Chrome
                        How to Google more effectively to get the results you need
                        But it can be tricky to anticipate what the experience of eating there will be like. Will it feel too crowded when you arrive? Does the lighting set the right mood? 

                        These are the sorts of questions Google is trying to answer with its new "immersive view" feature in Google Maps. 

                        The new feature, announced last year, is rolling out Tuesday starting in London, Los Angeles, New York, San Francisco, and Tokyo. 

                        In the coming months, it will launch in more cities, including Florence, Venice, Amsterdam, and Dublin.

                        Also: The best Android phones right now

                        Using AI, the feature fuses billions of Street View and aerial images, creating a rich, "immersive view" of the world. It uses neural radiance fields (NeRF), an advanced AI technique, to create 3D images out of ordinary pictures. This gives the user an idea of a place's lighting, the texture of materials, or pieces of context, such as what's in the background.

                        Image: Google
                        Google will soon expand the Search with Live View in Maps to more places in Europe, including Barcelona, Madrid, and Dublin. Additionally, Indoor Live View is expanding to more 1,000 new airports, train stations, and malls in a variety of cities, including London, Paris, Berlin, Madrid, Barcelona, Prague, Frankfurt, Tokyo, Sydney, Melbourne, São Paulo, and Taipei.

                        Maps is also getting new features for EV drivers. The platform will show you places that have on-site charging stations and will help you find chargers of 150 kilowatts or higher. 

                        Google is also stepping up the ways you can explore the world with Lens, the AI-powered tool that lets people conduct an image search from their camera or photos. First released in 2017, people already use Lens more than 10 billion times a month, Google said. 


                        With multisearch using Lens, people can search using text and images at the same time. Just a few months ago, Google launched "multisearch near me" to take a picture of something (like a specific meal) and find out where to find it locally. In the coming months, Google said it will roll out "multisearch near me" to all languages and countries where Lens is available. 

                        Multisearch is also expanding to images on the web on mobile. Additionally, Google is bringing a "search your screen" with the Lens feature to Android. Users will be able to search photos or videos on their screen, regardless of what app or website they're using -- without leaving the app.

                        Also: 3 things Google needs to fix for Android to catch up to iOS

                        Google Translate is also getting an update. Among other things, the tech giant shared on Wednesday that the tool will provide more context for translations. For instance, it will tell you if words or phrases have multiple meanings and help you find the best translation. This update will start rolling out in English, French, German, Japanese, and Spanish in the coming weeks.""",
                    
                    "cliffhanger":False
            }
        }


@router.post("/infer")
async def prompt(payload: GptInferenceType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls GPT with the prompt and returns inferred top 3 keywords, top 3 categories, sypnosis and blurb
    """
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    if not payload.text:
        logger.error("/infer Missing prompt")
        raise HTTPException(status_code=400, detail=f"Missing prompt")

    if payload.cliffhanger:
        cliff_hanger_text = "with a cliffhanger"
    else:
        cliff_hanger_text = ""

    prompt_prefix = f"""Translate if necessary, then summarize the article into a long english synopsis of 200 words and 
                        a short english blurb {cliff_hanger_text}. Do not quote and use line breaks if necessary.
                        Classify the original language used in the article, 
                        rank the top 3 relevant countries, 
                        rank the top 3 relevant keywords, 
                        rank the top 3 relevant categories, 
                        and indicate if the article is considered a tech news article. 
                        Pick categories from only this list of categories ["Cloud Computing & Infrastructure","Consumer Technology","Cyber Security & Privacy","Data Science & AI","Decentralized Computing","Digital Transformation & Innovation","Infocomm & Geospatial Technology","IoT, Robotics & Automation","IT & Network Infrastructure","Sector Applications","Software & App Development","Tech Gadgets and Accessories","Tech Organizations"]
                        Use only the following JSON template to respond:

                    {{
                    "language used":"",
                    "top 3 countries ranked":[],
                    "top 3 keywords ranked":[],
                    "top 3 categories ranked":[],
                    "tech article": true/false,
                    "synopsis":"",
                    "blurb":""
                    }}

                    ## START OF ARTICLE\n\n:
                    """
    
    prompt_suffix = "\n\n ## END OF ARTICLE"
    TEXT_MAX_CHARS = 10000

    text = payload.text[:TEXT_MAX_CHARS]

    prompt = prompt_prefix + text.replace("\"","'") + prompt_suffix

    model=GPT_MODEL_DEFAULT
    temperature=0 #Low temperature to get deterministic results
    max_tokens=GPT_MAX_TOKENS_DEFAULT #Limit response length
    top_p=GPT_TOP_P_DEFAULT
    frequency_penalty=GPT_FREQUENCY_PENALTY_DEFAULT
    presence_penalty=GPT_PRESENSE_PENALTY_DEFAULT

    try:
        print("prompt:",prompt)
        infer_response = await llm_util.gpt_completion(prompt, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
        print("response:",infer_response)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=502, detail=f"GPT API error: {e}")

    if infer_response: 
        id = infer_response.get("id")
        model = infer_response.get("model")
        created = infer_response.get("created")
        inferred_text = infer_response.get("choices")[0]["text"]
        tokens_used = infer_response.get("usage").get("total_tokens")

        # In case response contains additional text prefix (eg. "Response: {...}""), remove the prefix
        # inferred_text must be a JSON parsable string
        inferred_text = inferred_text[inferred_text.find('{'):]

        try:
            inferred_fields = json.loads(inferred_text,strict=False)
        except json.decoder.JSONDecodeError:
            # https://stackoverflow.com/questions/52636846/python-cant-parse-json-with-extra-trailing-comma
            import yaml
            inferred_fields = yaml.load(inferred_text)
        language = inferred_fields['language used']
        country = inferred_fields['top 3 countries ranked']
        keywords = inferred_fields['top 3 keywords ranked']
        categories = inferred_fields['top 3 categories ranked']
        is_tech_article = inferred_fields['tech article']
        sypnosis = inferred_fields['synopsis']
        blurb = inferred_fields['blurb']

        # Store records of GPT usage by storing caller, prompt, model and processed response
        model_gpt_inference.put_gpt_inference(id, prompt, model, temperature, language, country, keywords, categories, is_tech_article, sypnosis, blurb, caller, tokens_used, created)

        # Return GPT response
        return {
            "prompt": prompt,
            "model": model,
            "language": language,
            "country": country,
            "keywords": keywords,
            "categories": categories,
            "is_tech_article": is_tech_article,
            "sypnosis": sypnosis,
            "blurb": blurb,
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unknown error: {infer_response}",
        )
