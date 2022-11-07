__version__ = "0.1.dev05"

import http.server
import inspect
import logging
import re
import requests
import socketserver
import urllib.parse as urllib

from collections import namedtuple, defaultdict
from datetime import datetime

def func_name():
	return inspect.stack()[1].function

class TrackerRequest:
	class URL:
		class Query(dict):
			ValueCaster = namedtuple("ValueCaster", ("load", "dump"))
			KEY_CAST = {
				"info_hash": ValueCaster(urllib.unquote_to_bytes, urllib.quote_from_bytes),
				"peer_id": ValueCaster(urllib.unquote_plus, urllib.quote_plus),
				"port": ValueCaster(int, str),
				"cryptoport": ValueCaster(int, str),
				"uploaded": ValueCaster(int, str),
				"downloaded": ValueCaster(int, str),
				"left": ValueCaster(int, str),
				"numwant": ValueCaster(int, str),
				"key": ValueCaster(urllib.unquote_plus, urllib.quote_plus),
				"compact": ValueCaster(lambda s: bool(int(s)), lambda b: "1" if b else Ellipsis),
				"supportcrypto": ValueCaster(lambda s: bool(int(s)), lambda b: "1" if b else Ellipsis),
				"requirecrypto": ValueCaster(lambda s: bool(int(s)), lambda b: "1" if b else Ellipsis),
				"event": ValueCaster(urllib.unquote_plus, urllib.quote_plus),
				"ip": ValueCaster(urllib.unquote_plus, urllib.quote_plus),
				"ipv6": ValueCaster(urllib.unquote_plus, urllib.quote_plus),
			}

			def __init__(self, query_string):
				_dict = {}
				for item in query_string.split("&"):
					if "=" in item:
						key, value_str = item.split("=")
						value = self.KEY_CAST[key].load(value_str)
					else:
						key = item
						value = None
					
					if key in _dict:
						if isinstance(_dict[key], list):
							_dict[key].append(value)
						else:
							_dict[key] = [_dict[key], value]
					else:
						_dict[key] = value
				super().__init__(_dict)

			def __getattr__(self, key):
				return self[key]

			def __setattr__(self, key, value):
				self[key] = value

			def __str__(self):
				query_string_parts = []
				for key, v in self.items():
					if isinstance(v, list):
						values = v
					else:
						values = [v]

					for value in values:
						if value is None:
							query_string_parts.append(key)
						else:
							value_str = self.KEY_CAST[key].dump(value)
							if value_str is not Ellipsis:
								query_string_parts.append(f"{key}={value_str}")
				return "&".join(query_string_parts)

			def __repr__(self):
				return "".join(f"\t\t{key}: {value!r}\n" for key, value in self.items())

		def __init__(self, url_str):
			url = urllib.urlparse(url_str)
			self.server = f"{url.scheme}://{url.netloc}"
			self.endpoint = url.path.split("/")[-1]
			self.path = url.path[:-len(self.endpoint)]
			self.query = self.Query(url.query)

		def __str__(self):
			return f"{self.server}{self.path}{self.endpoint}?{self.query}"

		def __repr__(self):
			return f"\tserver: {self.server!r}\n\tpath: {self.path!r}\n\tendpoint: {self.endpoint!r}\n\tquery:\n{self.query!r}"

	def __init__(self, url, headers):
		self.url = self.URL(url)
		self.headers = dict(headers)

class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
	MEMORY = defaultdict(dict)

	@classmethod
	def apply_fake_ratio(cls, request):
		logger = logging.getLogger(f"{cls.__module__}.{cls.__qualname__}.{func_name()}")
		mem_id = request.url.query.info_hash.hex()

		if "downloaded" in request.url.query:
			request.url.query.downloaded = 0

		if "left" in request.url.query:
			if request.url.query.left != 0:
				if "left" not in cls.MEMORY[mem_id]:
					cls.MEMORY[mem_id]["left"] = request.url.query.left
				else:
					request.url.query.left = cls.MEMORY[mem_id]["left"]

			logger.debug(f"Fake ratio applied, new tracker request:\n{request.url!r}")

	@classmethod
	def process_request(cls, request):
		if request.url.endpoint == "announce":
			logger.debug(f"Tracker request:\n{request.url!r}")
			
			cls.apply_fake_ratio(request)

	@classmethod
	def process_response(cls, request, response):
		pass

	def do_GET(self):
		logger = logging.getLogger(f"{type(self).__module__}.{type(self).__qualname__}.{func_name()}")
		logger.info(f"Request: {self.requestline}")

		try:
			request = TrackerRequest(self.path, self.headers)

			self.process_request(request)

			response = requests.get(str(request.url), headers = request.headers)
			
			self.process_response(request, response)

			self.send_response(response.status_code)
			for k, v in response.headers.items():
				self.send_header(k, v)
			self.end_headers()
			self.wfile.write(response.content)

		except Exception as e:
			logger.exception(f"Error while processing '{self.path}'")

	def log_request(self, *args):
		pass

def daemon(listen_address, listen_port):
	logger = logging.getLogger(f"{__name__}.daemon")

	with socketserver.TCPServer((listen_address, listen_port), HTTPRequestHandler) as server:
		logger.info(f"Listening on {listen_address}:{listen_port}")
		server.serve_forever()