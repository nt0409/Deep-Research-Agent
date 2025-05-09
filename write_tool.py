from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class FileWriteToolInput(BaseModel):
    """Input schema for FileWriteTool."""
    file_path: str = Field(..., description="Path to the file where content will be written.")
    content: str = Field(..., description="Content to write to the file.")

class FileWriteTool(BaseTool):
    name: str = "File Writer Tool"
    description: str = "Writes content to a file with UTF-8 encoding for Unicode support."
    args_schema: Type[BaseModel] = FileWriteToolInput
    
    def _run(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, mode="w", encoding="utf-8") as file:
                file.write(content)
            return f"Successfully wrote content to {file_path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"