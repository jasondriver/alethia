import sawtooth_signing
import cbor
import hashlib
import urllib.request
from urllib.error import HTTPError
from sawtooth_sdk.protobuf.transaction_pb2 import (TransactionHeader, Transaction)
from sawtooth_sdk.protobuf.batch_pb2 import (BatchHeader, Batch, BatchList)
from sawtooth_signing import (CryptoFactory)
from sawtooth_signing.secp256k1 import (Secp256k1PrivateKey)

import yaml
import base64

# Generate a signer for this submitter
# (it's like a user wallet address in bitcoin?)
def make_private_key_hex():
  """Returns a brand-new private key in hex-encoded format."""
  context = sawtooth_signing.create_context('secp256k1')
  private_key = context.new_random_private_key()
  return private_key.as_hex()


def make_alethia_log_prefix(host, log):
  """
  Encodes a host/log pair as an Alethia object namespace. A specific page within
  this namespace can be identified by appending a 16-hex-digit index, zero-padded
  on the left.

  Example:
    x = make_alethia_log_prefix(host="www.jonathan.com", log="syslog")
    assert x == "117169162466aaf52f49f147a51c0a4e163e6083c6868329547349"
  """
  family = hashlib.sha512("alethia".encode("utf-8")).hexdigest()[0:6]
  scope = hashlib.sha512(cbor.dumps({"host": host, "log": log})).hexdigest()[0:48]
  log_prefix = family + scope
  return log_prefix

def unpack_page_object(page_object):
  addrs, data = page_object.split(b"|", 1)
  prev_addr, next_addr = addrs.split(b",", 1)
  return {
    "prev": prev_addr.decode("utf-8"),
    "next": next_addr.decode("utf-8"),
    "data": data.decode("utf-8").split(","),
  }

class Alethia(object):
  """
  An `Alethia` object represents the interactions of a client with an Alethia
  blockchain instance. The Alethia instance is identified by the URL of its REST
  API, and the client is identified by a private key.
  """

  def __init__(self, host, private_key_hex, *, api_url):
    """
    Initializes an Alethia client context.

    host: A globally-unique string identifying the host whose logs are to be accessed.
    private_key_hex: A hex-encoded private key to use for signing transactions.
    api_url: The URL of the Sawtooth API. Example: "http://rest-api:8008"
    """
    context = sawtooth_signing.create_context('secp256k1')
    private_key = Secp256k1PrivateKey.from_hex(private_key_hex)

    self._host = host
    self._signer = CryptoFactory(context).new_signer(private_key)
    self._api_url = api_url

  def get_log_handle(self, log, last_transaction_sig=None):
    """
    Returns a handle to an Alethia log object.
    log: A log path uniquely identifying this log relative to the host.
    last_transaction_sig: The header signature of a transaction that must commit
      before any subsequent appends to this log should be processed on the blockchain.

    Example:
      log = alethia.get_log_handle("syslog")
    """
    log_prefix = make_alethia_log_prefix(self._host, log)
    return AlethiaLog(self._api_url, self._signer, log_prefix, last_transaction_sig)

class AlethiaLog(object):
  """
  An `AlethiaLog` object represents a single log stored in the Alethia blockchain.
  It is more convenient to obtain `AlethiaLog` objects through the `Alethia#get_log_handle`
  method than to construct one directly.
  """

  def __init__(self, api_url, signer, log_prefix, last_transaction_sig=None):
    """
    Constructs an AlethiaLog handle to a blockchain-backed log.

    api_url: The URL of the Sawtooth API. Example: "http://rest-api:8008"
    signer: A sawtooth_signing.Signer instance.
    log_prefix: An address namespace identifying all pages within this log.
    last_transaction_sig: The header signature of a transaction that must commit
      before any subsequent appends should be processed on the blockchain.
    """
    self._api_url = api_url
    self._signer = signer
    self._log_prefix = log_prefix
    self._last_transaction = last_transaction_sig

  def get_last_transaction_sig():
    """
    Get the header signature of the last transaction performed. It's important to
    persist this between runs of the logger so that logs don't get committed out
    of order. Pass this to the constructor of `AlethiaLog` when the system comes
    back up.
    """
    return self._last_transaction

  def append(self, data):
    """
    Appends an integrity proof to the Alethia blockchain.

    data: A blob to be appended to the log.
    """
    # Prepare the payload
    payload_bytes = cbor.dumps({
      "action": "append",
      "log_id": self._log_prefix,
      "data": data,
    })

    # Build the transaction
    transaction_header_bytes = TransactionHeader(**{
      "family_name": "alethia",
      "family_version": "0.0.1",

      # In this example, we're signing the batch with the same private key,
      # but the batch can be signed by another party, in which case, the
      # public key will need to be associated with that key.
      "signer_public_key": self._signer.get_public_key().as_hex(),
      "batcher_public_key": self._signer.get_public_key().as_hex(),

      # In this example, there are no dependencies.  This list should include
      # any previous transaction header signatures that must be applied for
      # this transaction to successfully commit.
      # For example,
      # dependencies=['540a6803971d1880ec73a96cb97815a95d374cbad5d865925e5aa0432fcf1931539afe10310c122c5eaae15df61236079abbf4f258889359c4d175516934484a'],
      # (in our case, the previous log entry)
      "dependencies": [self._last_transaction] if self._last_transaction is not None else [],

      # Inputs/outputs specify objects (not transactions) that this transaction
      # depends on.
      # (in our case, we depend on the log namespace being appended to)
      "inputs": [self._log_prefix],
      "outputs": [self._log_prefix],

      "payload_sha512": hashlib.sha512(payload_bytes).hexdigest(),
    }).SerializeToString()

    transaction_header_signture = self._signer.sign(transaction_header_bytes)
    transaction = Transaction(**{
      "header": transaction_header_bytes,
      "header_signature": transaction_header_signture,
      "payload": payload_bytes,
    })

    # Create a batch to contain the transaction
    # Ironically, a batch is more like a transaction than a transaction is.
    # A transaction represents an operation to perform; a batch represents a set of
    # operators for which either all operations commit, or none do.
    batch_header_bytes = BatchHeader(**{
      "signer_public_key": self._signer.get_public_key().as_hex(),
      "transaction_ids": [transaction.header_signature],
    }).SerializeToString()

    batch = Batch(**{
      "header": batch_header_bytes,
      "header_signature": self._signer.sign(batch_header_bytes),
      "transactions": [transaction],
    })

    # `batch_list_bytes` is what must be submitted to the validator.
    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()

    try:
      request = urllib.request.Request(
        self._api_url + "/batches",
        batch_list_bytes,
        method="POST",
        headers={"Content-Type": "application/octet-stream"}
      )
      response = urllib.request.urlopen(request)
      # Store this transaction so our next transaction can state a dependency on it.
      self._last_transaction = transaction_header_signture
      print(response)
      return True
    except HTTPError as e:
      print(e)
      return False

  def get_page(self, index):
    """
    Gets the designated page of log contents.
    Returns `{prev: ADDRESS, next: ADDRESS, data: [BLOBS]}`
    """
    try:
      request = urllib.request.Request(
        self._api_url + "/state/" + self._log_prefix + "{:016x}".format(index),
        method="GET"
      )
      response = urllib.request.urlopen(request)
      print ("status:", response.status)
    except HTTPError as e:
      print(e)
      return False
    ydata = yaml.load(response.read(3000000).decode('utf-8'))
    obj = unpack_page_object(base64.b64decode(ydata["data"]))
    return obj["data"] # returns just data in list
    #return {k: obj[k] for k in ["head", "tail", "data"]}

if __name__ == "__main__":
  # Testing!
  private_key_hex = make_private_key_hex()
  alethia = Alethia("www.jonathan.com", private_key_hex, api_url="http://rest-api:8008")
  log = alethia.get_log_handle("syslog")
  print(log.append("BLAHBLAHBLAH"))
  print(log.get_page(0))
