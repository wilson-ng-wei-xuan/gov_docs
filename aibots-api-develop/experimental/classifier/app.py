from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from src.inference.inference import PromptClassifier
from pydantic import BaseModel

prefix = "hallucination-risk"
app = FastAPI(
    #root_path=f"/{prefix}",
    docs_url=f"/{prefix}/docs",
    redoc_url=None,
    openapi_url=f"/{prefix}/openai.json" 
    )

# Load a pre-trained ResNet model
prompt_classifier = PromptClassifier()

class TextInput(BaseModel):
    text: str


@app.get(f"/{prefix}")
async def read_root():
    return {"message": "Welcome to the Classifier!"}

@app.get(f"/{prefix}/predict")
async def predict(input_text: str):
    try:
        output_string = prompt_classifier.run_pipeline(input_text)

        # Return the result as JSON
        return JSONResponse(content=jsonable_encoder({"result": output_string}))

    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"/{prefix}/create_embeddings")
async def predict(input_text: str):
    try:
        output_list = prompt_classifier.create_embeddings(input_text)

        # Return the result as JSON
        return JSONResponse(content={"embeddings": output_list})

    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=str(e))
