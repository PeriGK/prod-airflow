# VERSION 1.10.3
# AUTHOR: Ryan Kelly
# DESCRIPTION: Basic Airflow container
# BUILD: docker build --rm -t rkells/prod-airflow .
# SOURCE: https://github.com/r-kells/prod-airflow

FROM python:3.7-slim
LABEL maintainer="Ryan Kelly"

# Never prompts the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

# Airflow
ARG AIRFLOW_VERSION=1.10.3
ARG AIRFLOW_USER_HOME=/usr/local/airflow
ARG PYTHON_DEPS=""
ENV AIRFLOW_HOME=${AIRFLOW_USER_HOME}

RUN set -ex \
    && buildDeps=' \
        freetds-dev \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
    ' \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
        $buildDeps \
        freetds-bin \
        build-essential \
        apt-utils \
        netcat \
        curl \
        git \
        ssh \
    && useradd -ms /bin/bash -d ${AIRFLOW_USER_HOME} airflow \
    && pip install -U "pip==19.1.1" "setuptools==41.0.1" \
    && pip install -U "flake8==3.6.0" "pep8-naming==0.7.0" "coverage==4.5.3" \
    && pip install "pytz==2019.1" \
    && pip install "pyOpenSSL==19.0.0" \
    && pip install "ndg-httpsclient==0.5.1" \
    && pip install "pyasn1==0.4.5" \
    && pip install apache-airflow[async,crypto,celery,google_auth,password,postgres,jdbc,redis,s3,slack,ssh]==${AIRFLOW_VERSION} \
    && pip install 'werkzeug>=0.15.0' \
    && if [ -n "${PYTHON_DEPS}" ]; then pip install ${PYTHON_DEPS}; fi \
    && apt-get purge --auto-remove -yqq $buildDeps \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

COPY script/entrypoint.sh /entrypoint.sh
COPY config/airflow.cfg ${AIRFLOW_USER_HOME}/airflow.cfg
COPY setup.cfg ${AIRFLOW_USER_HOME}/setup.cfg

RUN chown -R airflow: ${AIRFLOW_USER_HOME}

EXPOSE 8080 5555 8793

USER airflow
WORKDIR ${AIRFLOW_USER_HOME}
ENTRYPOINT ["/entrypoint.sh"]
CMD ["webserver"] # set default arg for entrypoint
HEALTHCHECK CMD curl -sLf http://localhost:8080/health || exit 1
