from fastapi import FastAPI, Body
import uvicorn
import uuid
from src.service.tasks import do_fitting_task

app = FastAPI(title="galfits fitting service", version="1.0")

def validate_arguments(meta_data: dict):
    fitting_mode = meta_data.get("FittingMode", "").lower()
    if fitting_mode not in ["image fitting", "pure sed fitting", "image sed fitting"]:
        return False, "FittingMode is required and must be one of 'image fitting', 'pure sed fitting', or 'image sed fitting'"

    lyric_file = meta_data.get("LyricFile", None)
    if lyric_file is None:
        return False, "LyricFile path is required in meta_data"
    workplace = meta_data.get("Workplace", None)
    if workplace is None:
        return False, "Workplace path is required in meta_data"    

    callback_url = meta_data.get("CallbackURL", None)
    if callback_url is None or not callback_url.startswith("http"):
        return False, "CallbackURL must be a valid URL starting with http or https"    

    return True, ""    

@app.post("/api/fitting/", summary="fitting interface")
async def fitting_process(body: dict = Body(...)):
    meta_data = body.get("meta", None)
    if meta_data is None:
        return {"status": "error", "message": "meta data not specified!"}
    valid, message = validate_arguments(meta_data)
    if not valid:
        return {"status": "error", "message": message}
        
    task_id = uuid.uuid4().hex
    task = do_fitting_task.delay(task_id=task_id, data=meta_data)
    return {"status": "success", "task_id": task.id, "message": "Fitting task has been submitted successfully."}

@app.get("/api/fitting-status/{task_id}")
def status(task_id: str):
    res = do_fitting_task.AsyncResult(task_id)
    return {"status": res.status, "result": res.result}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
