import base64
import json
from typing import Optional

from fastapi import APIRouter, Security, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, AnyHttpUrl
from fastapi.responses import RedirectResponse

from app import config
from app.models.summary.summary_model import GptSummaryModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import dynamodb, TABLE_MOONSHOT_LLM, GPT_MODEL_DEFAULT, GPT_TEMPERATURE_DEFAULT, GPT_MAX_TOKENS_DEFAULT, GPT_TOP_P_DEFAULT, GPT_FREQUENCY_PENALTY_DEFAULT, GPT_PRESENSE_PENALTY_DEFAULT
import logging

from app.config import logger

router = APIRouter()
security_http_bearer = HTTPBearer()

model_gpt_summary = GptSummaryModel(dynamodb, TABLE_MOONSHOT_LLM)

class GptSummarizeType(BaseModel):
    text: str

    class Config:
        schema_extra = {
            "example": {
                "text": """The Data Science and Artificial Intelligence Division (DSAID) was established as a capability centre to enable GovTech and the whole-of-government (WOG) to formulate effective policies and deliver citizen-centric services through data-driven insights and decision-making. This will allow evidence-based policy making, enhanced productivity in public service provision and better targeted services to meet citizens' needs.

                            We work with government agencies in using data science and artificial intelligence to improve policy outcomes, service delivery and operational efficiency, as well as build intelligent platforms to add value to the work of partner agencies.

                            We support agencies in building in-house data science expertise, formulating data strategies and setting up the necessary data infrastructure.

                            We are organised into five teams - Quantitative Strategy, Capability Development, Artificial Intelligence (AI) Platforms, Video Analytics and Data Engineering - that work in a fast-paced and an outcome-driven manner. We are driven by the “so what” and make sure that our findings and models can be translated into tangible impact. We start small and move fast; if a product works, we would scale them. If not, we would examine what could have gone wrong and what could be done better next time.

                            Working in evolving tech fields requires our teams to learn continuously about new architectures, frameworks, technologies and languages, as well as draw from the deep domain knowledge of partners and best practices from our community of experts.

                            DSAID has been instrumental in supporting WOG digital transformation and delivering #techforpublicgood, specifically through:

                            Government agency DSAI consultancy projects
                            Incubation of AI tech solutions such as Vigilant Gantry, an automated temperature screening access control system that also interfaces with face recognition for identification, and a WOG 'super' virtual assistant, VICA
                            Development and deployment of data-driven products and WOG platforms such as a central and secure data exploitation platform
                            Empower public officers and agencies to be more data-driven, through building up a strong data community and spearheading data training, bootcamps, and competitions.
                            Follow our Medium blog, where we share on our Data Science and AI work: https://medium.com/dsaid-govtech

                            Here are some of the roles we are hiring for:

                            Data Engineer
                            Data Scientist
                            Quantitative Analyst
                            Artificial Intelligence (AI) Engineer""",
            }
        }


@router.post("/summarize")
async def prompt(payload: GptSummarizeType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls GPT with the prompt and returns the summary
    """
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    if not payload.text:
        logger.error("/summarize Missing prompt")
        raise HTTPException(status_code=400, detail=f"Missing prompt")

    prompt_prefix = ""
    prompt_suffix = "\n\nTl;dr\n"
    TEXT_MAX_CHARS = 6000

    text = payload.text[:TEXT_MAX_CHARS]

    prompt = prompt_prefix + text.replace("\"","'") + prompt_suffix

    model=GPT_MODEL_DEFAULT
    temperature=GPT_TEMPERATURE_DEFAULT
    max_tokens=GPT_MAX_TOKENS_DEFAULT
    top_p=GPT_TOP_P_DEFAULT
    frequency_penalty=GPT_FREQUENCY_PENALTY_DEFAULT
    presence_penalty=GPT_PRESENSE_PENALTY_DEFAULT

    try:
        summarize_response = await llm_util.gpt_completion(prompt, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
        print(summarize_response)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=502, detail=f"GPT API error: {e}")

    if summarize_response: 
        id = summarize_response.get("id")
        created = summarize_response.get("created")
        summary_text = summarize_response.get("choices")[0]["text"]
        tokens_used = summarize_response.get("usage").get("total_tokens")

        # Store records of GPT usage by storing user, prompt, model and response
        model_gpt_summary.put_gpt_summary(id, prompt, model, temperature, summary_text, caller, tokens_used, created)

        # Return GPT response
        return {
            "prompt": prompt,
            "model": model,
            "summary": summary_text,
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unknown error: {summarize_response}",
        )
