from fastapi import APIRouter, HTTPException
from app.models.todo import WorkerData, received_data

router = APIRouter()

@router.post("/programmer/send")
def send_info(data: WorkerData):
    name = data.worker_name
    file = data.file_name
    
    if name not in received_data:
        raise HTTPException(status_code=404, detail=f"Worker '{name}' not found!")
        
    if name == "Pochta":
        received_data["Pochta"]["mp3_player"] = file
    else:
        received_data[name] = file
        
    return {"status": "Erfolg", "received_file": file}


@router.get("/pochta/listen")
def pochta_listen_music():
    mp3 = received_data["Pochta"]["mp3_player"]
    
    if not mp3:
        return {"status": "Meldung", "audio": "Player is empty..."}
        
    return {"status": "Erfolg", "audio": f"Simulation: File {mp3} played!"}
