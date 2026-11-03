FROM python:3.12-slim
RUN useradd -u 10001 -m runner
COPY pubdata.py /opt/lib/pubdata.py
ENV PYTHONPATH=/opt/lib PYTHONDONTWRITEBYTECODE=1
USER runner
WORKDIR /tmp
ENTRYPOINT ["python", "-I", "-c", "import sys,runpy; sys.path.insert(0,'/opt/lib'); exec(sys.stdin.read())"]
