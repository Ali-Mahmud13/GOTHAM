import asyncio
from fetch_data import fetch_patient_data



async def test_fetch_patient_data():
    patient_id = "P004" 

    result = await fetch_patient_data(patient_id)

    if not result:
        print(f"No data found for Patient ID: {patient_id}")
    else:
        print(f"Data for Patient {patient_id}:")
        for key, value in result.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_fetch_patient_data())
