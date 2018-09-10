# Copyright 2016 Intel Corporation
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

import logging
import hashlib

import cbor
import json  # for debugging


from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError


LOGGER = logging.getLogger(__name__)

FAMILY_NAME = 'alethia'
ALETHIA_VERSION = '0.0.1'
ALETHIA_ADDRESS_PREFIX = \
  hashlib.sha512(
    FAMILY_NAME.encode('utf-8')
  ).hexdigest()[0:6]


# maximum number of elements per page
MAX_PAGE_SIZE = 1024

def unpack_page_object(page_object):
  meta, data = page_object.split(b"|", 1)
  prev_addr, next_addr, size = meta.split(b",", 2)
  return {
    "prev": prev_addr.decode("utf-8"),
    "next": next_addr.decode("utf-8"),
    "size": int(size, 10),
    "data": data,
  }

def pack_page_object(page):
  return (
      page["prev"].encode("utf-8")
    + b","
    + page["next"].encode("utf-8")
    + b","
    + str(page["size"]).encode("utf-8")
    + b"|"
    + page["data"]
  )


class AlethiaTransactionHandler(TransactionHandler):
  @property
  def family_name(self):
    return FAMILY_NAME

  @property
  def family_versions(self):
    return [ALETHIA_VERSION]

  @property
  def namespaces(self):
    return [ALETHIA_ADDRESS_PREFIX]

  def apply(self, transaction, context):
    # key:object pairs to submit back to the context
    changes = {}

    signer = transaction.header.signer_public_key
    payload = cbor.loads(transaction.payload)
    # LOGGER.debug("Received payload: {}".format(json.dumps(payload)))

    # log_id is an address prefix
    # head_addr is the address of the first page
    head_addr = payload["log_id"] + "{:016x}".format(0)
    # LOGGER.debug("First page: {}".format(head_addr))

    tags = context.get_state([head_addr])
    if len(tags) == 0:
      # For now, pretend a "create" action was issued
      head_page = {"prev": head_addr, "next": head_addr, "size": 0, "data": b""}
      changes[head_addr] = head_page
    else:
      head_page = unpack_page_object(tags[0].data)

    # LOGGER.debug("Contents of head: {}".format(head_page))

    tail_addr = head_page["prev"]
    # LOGGER.debug("Last page: {}".format(tail_addr))

    if tail_addr == head_addr:
      tail_page = head_page
    else:
      tags = context.get_state([tail_addr])
      if len(tags) == 0:
        raise InternalError("Unexpected dangling address")

      tail_page = unpack_page_object(tags[0].data)

    # LOGGER.debug("Contents of tail: {}".format(tail_page))

    if tail_page["size"] >= MAX_PAGE_SIZE:
      new_addr = payload["log_id"] +  "{:016x}".format(int(tail_addr[-16:], 16) + 1)
      new_page = {"prev": tail_addr, "next": head_addr, "size": 0, "data": b""}
      tail_page["next"] = new_addr
      head_page["prev"] = new_addr

      changes[head_addr] = head_page
      changes[tail_addr] = tail_page
      changes[new_addr] = new_page

      tail_addr = new_addr
      tail_page = new_page

    if tail_page["data"]:
      tail_page["data"] += b","
    tail_page["data"] += payload["data"].encode("utf-8")
    tail_page["size"] += 1

    changes[tail_addr] = tail_page
    # LOGGER.debug("New tail: {}".format(tail_page))

    context.set_state({k: pack_page_object(v) for k, v in changes.items()})

    LOGGER.debug("Appended to page {}".format(int(tail_addr[-16:], 16)))
