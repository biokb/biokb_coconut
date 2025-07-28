FROM python:3.12-alpine

# Set the working directory inside the container
WORKDIR /code

# Copy code
COPY src ./src/
COPY pyproject.toml README.md ./

RUN pip install .

# Start fastapi server
CMD ["fastapi", "run","src/biokb_coconut/api/main.py"]