FROM public.ecr.aws/lambda/python:3.12

COPY email-sender-agent.py ./

COPY download_invoice.py ./

COPY requirements.txt ./

RUN pip install -r requirements.txt
    
CMD ["email-sender-agent.handler"]
