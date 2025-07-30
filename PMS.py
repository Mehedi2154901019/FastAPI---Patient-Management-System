from fastapi import FastAPI, Path, HTTPException, Query
import json
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional
from fastapi.responses import JSONResponse

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description='ID of the patient', example='P001')]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the patient')]
    height: Annotated[float, Field(..., gt=0, description='Height of the patient in meters')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the patient in kgs')]


class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=120)]
    gender: Annotated[Optional[Literal['male', 'female', 'others']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]


def load_data():
    with open("patients.json", 'r') as f:
        data = json.load(f)
        return data


def save_data(data):
    with open("patients.json", 'w') as f:
        json.dump(data, f)


@app.get("/")
def intro():
    return {'message': 'Patient Management System API'}


@app.get("/about")
def about():
    return {'message': 'An API to manage patient records'}


@app.get('/view')
def view():
    data = load_data()
    return data


@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(..., description="ID of the patient", example='P001')):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404, detail='Patient Not Found')


@app.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description='Sort on the basis of height, weight, or bmi'),
    order: str = Query('asc', description='Sort in asc or desc order')
):
    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'Invalid field, select from {valid_fields}')

    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order, select 'asc' or 'desc'")

    data = load_data()

    # Calculate BMI dynamically if requested
    for patient in data.values():
        h = patient.get("height")
        w = patient.get("weight")
        if h and w:
            patient["bmi"] = round(w / (h ** 2), 2)

    reverse_order = True if order == 'desc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=reverse_order)

    return sorted_data


@app.post("/create")
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient already exists')

    data[patient.id] = patient.model_dump(exclude={'id'})
    save_data(data)

    return JSONResponse(status_code=201, content={'message': 'Patient created successfully'})


@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not Found")

    existing_patient_info = data[patient_id]
    updated_fields = patient_update.model_dump(exclude_unset=True)

    # Apply updates
    for key, value in updated_fields.items():
        existing_patient_info[key] = value

    # Reconstruct full patient object to validate
    existing_patient_info['id'] = patient_id
    patient_pydantic_object = Patient(**existing_patient_info)

    # Save updated patient info without ID
    data[patient_id] = patient_pydantic_object.model_dump(exclude={'id'})
    save_data(data)

    return JSONResponse(status_code=200, content={'message': 'Patient updated'})




@app.delete("/delete/{patient_id}")
def delete_patient(patient_id:str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail='Patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200,content={'message':'Patient deleted'})
