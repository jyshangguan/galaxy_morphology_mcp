FROM python:3.10-slim

WORKDIR /app


RUN apt-get update
RUN apt install -y vim git
RUN python -m pip install --upgrade pip
RUN pip install jax regions

#RUN git clone https://github.com/RuancunLi/GalfitS.git
COPY . .
RUN cd GalfitS && pip install -r requirement.txt

# 追加环境变量和别名到 ~/.bashrc
RUN echo 'export PYTHONPATH="/app/GalfitS/src:$PYTHONPATH"' >> ~/.bashrc && \
    echo 'export GS_DATA_PATH="/app/galfits-data"' >> ~/.bashrc && \
    echo 'alias galfits="python /app/GalfitS/src/galfits/galfitS.py --config "' >> ~/.bashrc

RUN pip install --no-cache-dir .

#CMD ["python", "src/mcp_server.py", "--transport", "http"]
