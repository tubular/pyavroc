APP_NAME := pyavroc
UNAME := $(shell uname)
AWS_PROFILE ?= default

###############################
######## VIRTUAL ENV ##########
###############################

APP_PATH := $(shell pwd)
VENV_PATH := $(APP_PATH)/venv_$(APP_NAME)
PIP_PATH := $(VENV_PATH)/bin/pip
PYTHON_PATH := $(VENV_PATH)/bin/python

venv: $(VENV_PATH)/reqs_installed

$(VENV_PATH)/reqs_installed: $(VENV_PATH)
	$(PIP_PATH) install --upgrade pip setuptools wheel pytest
	touch $(VENV_PATH)/reqs_installed

$(VENV_PATH):
	virtualenv -p $(shell which python3.5) -q $(VENV_PATH)

# NOTE(Christian): lint is the only thing that requires a venv
# don't want to move this to docker because it requires .git dir


###############################
####### NORMAL TARGETS ########
###############################

clean:
	@rm -rf $(VENV_PATH)
	@rm -rf .tox
	@rm -rf *.deb
	@rm -rf dist
	@rm -rf local_avro
	@rm -rf build
	@rm -rf .coverage htmlcov
	@find ./ -name __pycache__ | xargs rm -rf
	@find ./ -name \*.pyc | xargs rm -rf
	@rm -rf *.egg-info
	@echo "Cleaned package build artefacts."

###############################
######## BUILD TARGETS ########
###############################

export VENV_PYTHON=$(PYTHON_PATH)
build:	venv
	./build_apache_pyavro.sh --static

dist:	build
	$(PYTHON_PATH) setup.py bdist_wheel

publish:
	AWS_PROFILE=$(AWS_PROFILE) ./publish_wheel.sh $(JENKINS_HOST) $(JENKINS_JOB) $(S3_bucket)

.PHONY:	venv dist test lint clean
