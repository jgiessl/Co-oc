FROM python:3.8.7-buster

WORKDIR usr/src/app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./plotter.py .
COPY ./ranking_plots .

ENTRYPOINT ["python"]