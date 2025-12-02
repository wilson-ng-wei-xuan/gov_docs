from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app import config
# from app.api_v1.routers import routers as v1_api_router

from app.models.response.response_router import router as response_router
from app.models.summary.summary_router import router as summary_router
from app.models.inference.inference_router import router as inference_router
# from app.models.cohere.cohere_router import router as cohere_router
# from app.models.palm.palm_router import router as palm_router
from app.models.gpt.gpt_router import router as gpt_router
from app.models.apikey.apikey_router import router as apikey_router
from app.models.services.services_router import router as services_router
from app.models.h2oai.h2oai_router import router as h2oai_router
from app.models.lightgpt.lightgpt_router import router as lightgpt_router
from app.models.flan.flan_router import router as flan_router
from app.models.bloom.bloom_router import router as bloom_router
from app.models.stability.stability_router import router as stability_router
from app.models.llmstack.llmstack_router import router as llmstack_router

app = FastAPI(
    title='Moonshot API',
    description='API for Moonshot & Projects',
)

# Enable CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def get_root(response: Response):
    return {'message': f'Welcome to {config.APP_CODE}'}


# app.include_router(v1_api_router, prefix="/v1")
app.include_router(apikey_router, prefix="/apikey", tags=["Apikey"])
app.include_router(services_router, prefix="/services", tags=["API Services"])
app.include_router(response_router, prefix="/gpt", tags=["GPT"])
app.include_router(summary_router, prefix="/gpt", tags=["GPT"])
app.include_router(inference_router, prefix="/gpt", tags=["GPT"])
# app.include_router(cohere_router, prefix="/cohere", tags=["Cohere"])
# app.include_router(palm_router, prefix="/palm", tags=["PaLM"])
app.include_router(gpt_router, prefix="/gpt", tags=["GPT"])
app.include_router(h2oai_router, prefix="/h2oai", tags=["H2O.ai"])
app.include_router(lightgpt_router, prefix="/lightgpt", tags=["LightGPT"])
app.include_router(flan_router, prefix="/flan", tags=["FLAN"])
app.include_router(bloom_router, prefix="/bloom", tags=["Bloom"])
app.include_router(stability_router, prefix="/stability", tags=["Stability"])
app.include_router(llmstack_router, prefix="/llmstack", tags=["LLM-Stack"])

# Wrap API with Mangum
handler = Mangum(app)
