import shutil
import os
import uuid
import pandas as pd
from typing import List, Annotated
from pydantic import BaseModel
import logging  # Added for better logging

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS for frontend development (optional, adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount the static directory to serve static files (CSS, JS, HTML)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="static")

# Ensure the uploads directory exists
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


# --- Placeholder Processing Functions (Modified) ---

def process_excel_type_a(file_path: str, year: int, quarter: str) -> pd.DataFrame:
    """Processes Excel files with tag 'TypeA'."""
    logger.info(
        f"Processing Excel Type A for Year: {year}, Quarter: {quarter}, File: {file_path}")
    # Replace with your actual Excel processing logic
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        # Example: Add new columns based on input
        df['Processed_A'] = f"Processed by Type A for {year}-{quarter}"
        df['Year'] = year
        df['Quarter'] = quarter
        return df
    except Exception as e:
        logger.error(f"Error processing Excel Type A {file_path}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process Excel Type A file {os.path.basename(file_path)}: {e}")

# def process_excel_type_b(file_path: str, year: int, quarter: str) -> pd.DataFrame:
#     """Processes Excel files with tag 'TypeB'."""
#     logger.info(f"Processing Excel Type B for Year: {year}, Quarter: {quarter}, File: {file_path}")
#     try:
#         df = pd.read_excel(file_path)
#         df["Processed_B"] = f"Processed by Type B for {year}-{quarter}"
#         df['Year'] = year
#         df['Quarter'] = quarter
#         return df
#     except Exception as e:
#         logger.error(f"Error processing Excel Type B {file_path}: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to process Excel Type B file {os.path.basename(file_path)}: {e}")


# def process_pdf_type_c(file_path: str, year: int, quarter: str) -> pd.DataFrame:
#     """Processes PDF files with tag 'TypeC'."""
#     logger.info(f"Processing PDF Type C for Year: {year}, Quarter: {quarter}, File: {file_path}")
#     # Replace this with your PDF processing logic using PyPDF2 or another PDF library.
#     try:
#         # Example: Simulate extracting some data and adding year/quarter
#         # Real implementation would use a PDF library to extract text/tables
#         pdf_content_summary = f"Simulated PDF content from {os.path.basename(file_path)}"
#         data = {
#             'PDF_Summary': [pdf_content_summary],
#             'Processed_C': f"Processed by Type C for {year}-{quarter}",
#             'Year': [year],
#             'Quarter': [quarter]
#         }
#         df = pd.DataFrame(data)
#         return df
#     except Exception as e:
#         logger.error(f"Error processing PDF Type C {file_path}: {e}")
#         # Return an empty DataFrame or raise an error, depending on desired behavior
#         # raise HTTPException(status_code=500, detail=f"Failed to process PDF Type C file {os.path.basename(file_path)}: {e}")
#         return pd.DataFrame({'Error': [f"Failed to process PDF Type C: {e}"]})


# def process_pdf_type_d(file_path: str, year: int, quarter: str) -> pd.DataFrame:
#     """Processes PDF files with tag 'TypeD'."""
#     logger.info(f"Processing PDF Type D for Year: {year}, Quarter: {quarter}, File: {file_path}")
#     try:
#         # Example: Simulate extracting some data and adding year/quarter
#         pdf_content_summary = f"Simulated PDF content from {os.path.basename(file_path)}"
#         data = {
#             'PDF_Summary': [pdf_content_summary],
#             'Processed_D': f"Processed by Type D for {year}-{quarter}",
#             'Year': [year],
#             'Quarter': [quarter]
#         }
#         df = pd.DataFrame(data)
#         return df
#     except Exception as e:
#         logger.error(f"Error processing PDF Type D {file_path}: {e}")
#         # return pd.DataFrame({'Error': [f"Failed to process PDF Type D: {e}"]})
#         raise HTTPException(status_code=500, detail=f"Failed to process PDF Type D file {os.path.basename(file_path)}: {e}")

# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):  # Need request for templates
    """Serves the index.html file."""
    # Make sure you import Request from fastapi
    return templates.TemplateResponse("index.html", {"request": request})


class FileInfo(BaseModel):
    filename: str
    tag: str
    saved_path: str  # Added to store the actual path on the server

# Dependency to handle file uploads and basic validation


async def get_uploaded_files(
    # Use File(...) for required
    files: Annotated[List[UploadFile], File(...)],
    tags: Annotated[List[str], Form(...)],       # Use Form(...) for required
) -> List[FileInfo]:

    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    if len(files) != len(tags):
        raise HTTPException(
            status_code=400, detail="Number of files and tags must match.")

    file_info_list = []
    saved_files_paths = []  # Keep track of saved files for potential rollback on error

    try:
        for file, tag in zip(files, tags):
            if not file.filename:
                raise HTTPException(
                    status_code=400, detail="Received a file upload without a filename.")

            # Basic tag validation (optional but good)
            if not tag or tag not in ["TypeA", "TypeB", "TypeC", "TypeD"]:
                raise HTTPException(
                    status_code=400, detail=f"Invalid tag '{tag}' provided for file {file.filename}.")

            # Check if the file is one of the allowed types
            allowed_extensions = ('.xlsx', '.xls', '.pdf')
            file_ext = os.path.splitext(file.filename.lower())[1]
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400, detail=f"Invalid file type for {file.filename}. Only .xlsx, .xls, and .pdf are allowed.")

            # Validate tag/extension combinations (optional but recommended)
            if file_ext in ('.xlsx', '.xls') and tag not in ['TypeA', 'TypeB']:
                raise HTTPException(
                    status_code=400, detail=f"Tag '{tag}' is not valid for Excel file '{file.filename}'. Use TypeA or TypeB.")
            if file_ext == '.pdf' and tag not in ['TypeC', 'TypeD']:
                raise HTTPException(
                    status_code=400, detail=f"Tag '{tag}' is not valid for PDF file '{file.filename}'. Use TypeC or TypeD.")

            # Save file to a temporary location with a unique name
            unique_id = str(uuid.uuid4())
            # Sanitize filename slightly (optional)
            safe_filename = "".join(
                c for c in file.filename if c.isalnum() or c in ('.', '_', '-')).strip()
            if not safe_filename:
                safe_filename = "uploaded_file"  # Fallback
            file_path = os.path.join(
                UPLOADS_DIR, f"{unique_id}_{safe_filename}")

            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as e:
                logger.error(
                    f"Failed to save file {file.filename} to {file_path}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Could not save uploaded file {file.filename}.")
            finally:
                file.file.close()  # Ensure file handle is closed

            saved_files_paths.append(file_path)  # Add path to list
            file_info_list.append(
                FileInfo(filename=file.filename, tag=tag, saved_path=file_path))

        return file_info_list

    except HTTPException as http_exc:  # Catch validation errors specifically
        # Clean up any files saved *before* the error occurred
        for path in saved_files_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(
                        f"Cleaned up partially saved file due to error: {path}")
                except Exception as e_clean:
                    logger.error(
                        f"Failed to clean up file {path} after error: {e_clean}")
        raise http_exc  # Re-raise the validation error
    except Exception as e:
        # Clean up any files saved *before* the error occurred
        for path in saved_files_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(
                        f"Cleaned up partially saved file due to error: {path}")
                except Exception as e_clean:
                    logger.error(
                        f"Failed to clean up file {path} after error: {e_clean}")
        logger.error(f"Unexpected error during file upload processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred during file upload: {e}")


@app.post("/upload")
async def upload_files(
    year: Annotated[int, Form(...)],                # Added year form field
    quarter: Annotated[str, Form(...)],             # Added quarter form field
    file_info_list: List[FileInfo] = Depends(
        get_uploaded_files)  # Use the improved dependency
):
    """Handles file uploads and processing based on tags, year, and quarter."""

    processed_dataframes = []
    output_filename = None  # Define outside try block
    output_path = None

    # Basic validation for quarter (example)
    if quarter not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400, detail=f"Invalid quarter value: '{quarter}'. Must be Q1, Q2, Q3, or Q4.")
    # Basic validation for year (example)
    if not (2000 <= year <= 2099):
        raise HTTPException(
            status_code=400, detail=f"Invalid year value: '{year}'. Must be between 2000 and 2099.")

    logger.info(
        f"Received upload request for Year: {year}, Quarter: {quarter}")

    try:
        for file_info in file_info_list:
            logger.info(
                f"Processing file: {file_info.filename}, Tag: {file_info.tag}, Path: {file_info.saved_path}")

            if not os.path.exists(file_info.saved_path):
                # This should ideally not happen if get_uploaded_files worked, but check anyway
                logger.error(
                    f"File listed in FileInfo not found on server: {file_info.saved_path}")
                raise HTTPException(
                    status_code=404, detail=f"File {file_info.filename} (path: {file_info.saved_path}) not found on server.")

            df = None  # Initialize df for this file iteration
            file_ext = os.path.splitext(file_info.filename.lower())[1]

            # Process based on tag, file type, YEAR, and QUARTER
            if file_ext in ('.xlsx', '.xls'):
                if file_info.tag == 'TypeA':
                    # Call process_excel_type_a with year and quarter
                    df = process_excel_type_a(
                        file_info.saved_path, year, quarter)
                elif file_info.tag == 'TypeB':
                    # df = process_excel_type_b(file_info.saved_path, year, quarter) # Uncomment when implemented
                    # Placeholder if B is not implemented yet:
                    logger.warning(
                        f"Processing function for Excel Type B not implemented. Skipping file: {file_info.filename}")
                    # Example placeholder df
                    df = pd.DataFrame(
                        {'Info': [f'Type B processing not implemented for {year}-{quarter}']})
                # No need for 'else' here as tag/extension combo was validated in dependency

            elif file_ext == '.pdf':
                if file_info.tag == 'TypeC':
                    # df = process_pdf_type_c(file_info.saved_path, year, quarter) # Uncomment when implemented
                    logger.warning(
                        f"Processing function for PDF Type C not implemented. Skipping file: {file_info.filename}")
                    # Example placeholder df
                    df = pd.DataFrame(
                        {'Info': [f'Type C processing not implemented for {year}-{quarter}']})
                elif file_info.tag == 'TypeD':
                    # df = process_pdf_type_d(file_info.saved_path, year, quarter) # Uncomment when implemented
                    logger.warning(
                        f"Processing function for PDF Type D not implemented. Skipping file: {file_info.filename}")
                    # Example placeholder df
                    df = pd.DataFrame(
                        {'Info': [f'Type D processing not implemented for {year}-{quarter}']})
                # No need for 'else' here

            # Append the processed DataFrame if it exists
            if df is not None and not df.empty:
                processed_dataframes.append(df)
            else:
                logger.warning(
                    f"Processing for {file_info.filename} (Tag: {file_info.tag}) returned no data or was skipped.")

        # Combine all processed dataframes into one
        if not processed_dataframes:
            # Files might have been skipped or processing functions returned empty
            logger.warning("No data was generated after processing all files.")
            raise HTTPException(
                status_code=400, detail="No data generated. Files might have been skipped or processing resulted in empty data.")

        final_df = pd.concat(processed_dataframes, ignore_index=True)

        # Create the output Excel file
        output_filename = f"processed_output_{year}_{quarter}_{str(uuid.uuid4())}.xlsx"
        output_path = os.path.join(UPLOADS_DIR, output_filename)

        try:
            final_df.to_excel(output_path, index=False, engine="openpyxl")
            logger.info(f"Successfully created output file: {output_path}")
        except Exception as e:
            logger.error(
                f"Failed to write final DataFrame to Excel file {output_path}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate the output Excel file: {e}")

        # Return the generated Excel file
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            # FastAPI handles background task for cleanup after response automatically now
        )

    except HTTPException as http_exc:
        # Log and re-raise FastAPI/validation errors
        logger.error(
            f"HTTP Exception during processing: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Log unexpected errors during processing
        # Use logger.exception to include traceback
        logger.exception(
            f"An unexpected error occurred during file processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred during processing: {str(e)}")
    finally:
        # Clean up uploaded files
        for file_info in file_info_list:
            try:
                if file_info.saved_path and os.path.exists(file_info.saved_path):
                    os.remove(file_info.saved_path)
                    logger.info(
                        f"Cleaned up uploaded file: {file_info.saved_path}")
            except Exception as e:
                # Log error but don't prevent response/other cleanup
                logger.error(
                    f"Failed to remove uploaded file {file_info.saved_path} during cleanup: {e}")

        # Clean up the generated output file *if it exists* and wasn't sent successfully
        # Note: FileResponse usually handles this if it sends successfully, but belt-and-suspenders
        # This cleanup is tricky here because FileResponse might need the file *after* this block runs.
        # A BackgroundTask in the return statement is the more robust way for output file cleanup.
        # Let's rely on FileResponse's cleanup for the output file for now. If issues arise, use BackgroundTasks.
        # Example using BackgroundTasks (would need `from fastapi import BackgroundTasks`):
        # async def cleanup_output(path: str):
        #     if path and os.path.exists(path):
        #         try:
        #             os.remove(path)
        #             logger.info(f"Cleaned up output file via background task: {path}")
        #         except Exception as e:
        #             logger.error(f"Background task failed to remove output file {path}: {e}")
        # ... in upload_files return statement:
        # return FileResponse(..., background=BackgroundTask(cleanup_output, output_path))


# --- Run the Server (using uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    # Add reload=True for development convenience
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
