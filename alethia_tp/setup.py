# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
import os
import subprocess

from setuptools import setup, find_packages

data_files = []

if os.path.exists("/etc/default"):
  data_files.append(
    ( "/etc/default",
      ["packaging/systemd/alethia-tp"]
    )
  )

if os.path.exists("/lib/systemd/system"):
  data_files.append(
    ( "/lib/systemd/system",
      ["packaging/systemd/alethia-tp.service"]
    )
  )

setup(
  name="alethia-tp",
  version="0.0.1",
  description="Alethia Transaction Processor for Hyperledger Sawtooth",
  author="Hyperledger Sawtooth",
  url="",
  packages=find_packages(),
  install_requires=[
    "cbor",
    "colorlog",
    "sawtooth-sdk",
    "sawtooth-signing",
  ],
  data_files=data_files,
  entry_points={
    "console_scripts": [
      "alethia-tp = alethia_tp.processor.main:main"
    ]
  }
)
