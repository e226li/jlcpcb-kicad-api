import shutil

from fastapi import FastAPI, HTTPException, Security, status, Request
import yaml
from fastapi.security import APIKeyHeader
from starlette.responses import RedirectResponse, FileResponse
import subprocess

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key")

with open("keys.yaml") as f:
    api_keys = yaml.safe_load(f)


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("docs")


@app.get("/add-part")
async def add_part(jlcpcb_id: str, download_zip: bool = True, api_key: str = Security(get_api_key)):
    if not jlcpcb_id[1:].isnumeric():
        raise ValueError

    subprocess_object = subprocess.run(["JLC2KiCadLib", jlcpcb_id], capture_output=True, text=True)
    if subprocess_object.returncode != 0:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=subprocess_object.stderr)

    await regenerate_zip()

    if download_zip:
        return await download()


@app.get("/regenerate-zip")
async def regenerate_zip(api_key: str = Security(get_api_key)):  # TODO: lock
    shutil.make_archive("library-new", "zip", "JLC2KiCad_lib")

@app.get("/download")
async def download(regenerate: bool = False, api_key: str = Security(get_api_key)):
    if regenerate:
        await regenerate_zip()

    return FileResponse("library-new.zip", media_type="application/octet-stream", filename="library-new.zip")
