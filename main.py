from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import pandas as pd
from typing import List, Annotated
from pydantic import BaseModel
# Placeholder for PDF processing (using PyPDF2 as an example)

app = FastAPI()


# Mount the static directory to serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="static")

# Ensure the uploads directory exists
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


# --- Placeholder Processing Functions ---

def process_excel_type_a(file_path: str) -> pd.DataFrame:
    """Processes Excel files with tag 'TypeA'."""
    # Replace with your actual Excel processing logic
    df = pd.read_excel(file_path, engine="openpyxl")
    # Example: Add a new column
    df['Processed_A'] = "Processed by Type A"
    return df

# def process_excel_type_b(file_path: str) -> pd.DataFrame:
#     """Processes Excel files with tag 'TypeB'."""
#     df = pd.read_excel(file_path)
#     df["Processed_B"] = "Processed by Type B"
#     return df


# def process_pdf_type_c(file_path: str) -> pd.DataFrame:
#     """Processes PDF files with tag 'TypeC'."""
#     # Replace this with your PDF processing logic using PyPDF2 or another PDF library.
#     try:
#         with open(file_path, 'rb') as f:
#             data = f.read()
#             df = pd.DataFrame(data)
#             df['Processed_D'] = "Processed by Type D"
#             return df


    # except Exception as e:
    #     print(f"Error processing PDF: {e}")
    #     return pd.DataFrame()
    # #  return pd.DataFrame({'Text': [text_content]}) # Return an empty DataFrame if there's an error


# def process_pdf_type_d(file_path: str) -> pd.DataFrame:
#     """Processes PDF files with tag 'TypeD'."""
#     try:
#         with open(file_path, 'rb') as f:
#             data = f.read()
#             df = pd.DataFrame(data)
#             df['Processed_D'] = "Processed by Type D"
#             return df


#     except Exception as e:
#         print(f"Error processing PDF: {e}")
#         return pd.DataFrame()

# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the index.html file."""
    return templates.TemplateResponse("index.html", {"request": {}})


class FileInfo(BaseModel):
    filename: str
    tag: str

#Dependency
async def get_uploaded_files(
    files: Annotated[List[UploadFile], File()],
    tags: Annotated[List[str], Form()]
) -> List[FileInfo]:

    if len(files) != len(tags):
        raise HTTPException(status_code=400, detail="Number of files and tags must match.")

    file_info_list = []
    for file, tag in zip(files, tags):
        file_info_list.append(FileInfo(filename=file.filename, tag=tag))
        # Check if the file is one of the allowed types
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf')):
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Only .xlsx, .xls, and .pdf are allowed.")

        # Save file to a temporary location
        file_path = os.path.join(UPLOADS_DIR, str(uuid.uuid4()) + "_" + file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()  # Close the file after saving

    return file_info_list

@app.post("/upload")
async def upload_files(file_info_list: List[FileInfo] = Depends(get_uploaded_files)):
    """Handles file uploads and processing based on tags."""

    processed_dataframes = []
    try:
        for file_info in file_info_list:
            file_path = ""
            for filename in os.listdir(UPLOADS_DIR):
                if filename.endswith(file_info.filename):
                    file_path = os.path.join(UPLOADS_DIR, filename)
                    break
            print('0')
            
            if not file_path:
                raise HTTPException(status_code=404, detail=f"File {file_info.filename} not found on server.")
            print('1')

            # Process based on tag and file type
            if file_info.filename.lower().endswith(('.xlsx', '.xls')):
                print('2')
                
                if file_info.tag == 'TypeA':
                    df = process_excel_type_a(file_path)
                    processed_dataframes.append(df)
                    print('3')
                    
                elif True:
                    print('4')
                elif file_info.tag == 'TypeB':
                    # df = process_excel_type_b(file_path)
                    processed_dataframes.append(df)
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid tag '{file_info.tag}' for Excel file {file_info.filename}.")
            
            elif file_info.filename.lower().endswith('.pdf'):
                if file_info.tag == 'TypeC':
                    # df = process_pdf_type_c(file_path)
                    processed_dataframes.append(df)
                elif file_info.tag == 'TypeD':
                    # df = process_pdf_type_d(file_path)
                    processed_dataframes.append(df)
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid tag '{file_info.tag}' for PDF file {file_info.filename}.")
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type for {file_info.filename}.")

        # Combine all processed dataframes into one
        if processed_dataframes:
            final_df = pd.concat(processed_dataframes, ignore_index=True)
        else:
             raise HTTPException(status_code=400, detail="No file uploaded or processed.")

        # Create the output Excel file
        output_filename = "processed_output_" + str(uuid.uuid4()) + ".xlsx"
        output_path = os.path.join(UPLOADS_DIR, output_filename)
        final_df.to_excel(output_path, index=False)

        return FileResponse(path=output_path, filename=output_filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        print(f"An error on processing: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {str(e)}")
    finally:
        #Clean up
        for file_info in file_info_list:
            file_path = ""
            for filename in os.listdir(UPLOADS_DIR):
                if filename.endswith(file_info.filename):
                    file_path = os.path.join(UPLOADS_DIR, filename)
                    break
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"failed to remove {file_path} due to {e}")

# --- Run the Server (using uvicorn) ---
#  uvicorn main:app --reload --port 8000
# To run:  python main.py
#           Open browser to http://localhost:8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)