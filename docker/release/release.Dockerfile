ARG PYTHON_VERSION=3.9
ARG PACKAGE=omniverse

FROM python:${PYTHON_VERSION}

ARG PACKAGE
RUN pip install ${PACKAGE}
