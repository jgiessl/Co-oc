FROM python:3.8.7-buster

# Make directory
WORKDIR usr/src/app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

RUN mkdir temp_result

# Copy source code
COPY ./environment_process.py .
COPY ./main_program.py .
COPY ./matcher.py .
COPY ./object_process.py .
COPY ./training.py .

ENTRYPOINT ["python"]