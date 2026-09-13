from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool
from rembg import remove, new_session
from PIL import Image
import io

app = FastAPI(
    title="RemBG API",
    description="Background removal API for RemBG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = None


@app.get("/")
def root():
    return {
        "name": "RemBG API",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def get_session():
    global session

    if session is None:
        session = new_session("u2netp")

    return session


def process_image(image):
    rembg_session = get_session()
    return remove(image, session=rembg_session)


@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image."
        )

    try:
        image_data = await file.read()

        image = Image.open(io.BytesIO(image_data))
        image.load()

        result = await run_in_threadpool(process_image, image)

        output = io.BytesIO()
        result.save(output, format="PNG")

        return Response(
            content=output.getvalue(),
            media_type="image/png",
            headers={
                "Content-Disposition": 'inline; filename="rembg-result.png"'
            }
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Background removal failed: {str(error)}"
        )
