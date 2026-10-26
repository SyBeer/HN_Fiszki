FROM python:3.13-slim

WORKDIR /app
COPY results/results.py ./
RUN mkdir /data && chown nobody /data

USER nobody
EXPOSE 8000
CMD ["python", "-u", "results.py"]
