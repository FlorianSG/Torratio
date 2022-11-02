import ipaddress
import http.server
import logging
import re
import requests
import socketserver
import urllib.parse as urllib

from collections import namedtuple, defaultdict
from datetime import datetime

class TrackerQuery(dict):
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
			_dict[key] = value
		super().__init__(_dict)

	def build(self):
		query_string_parts = []
		for key, value in self.items():
			if value is None:
				query_string_parts.append(key)
			else:
				value_str = self.KEY_CAST[key].dump(value)
				if value_str is not Ellipsis:
					query_string_parts.append(f"{key}={value_str}")
		return "&".join(query_string_parts)

	def __str__(self):
		return "".join(f"\t{key}: {value}\n" for key, value in self.items()) + "\n"

class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
	MEMORY = defaultdict(dict)

	@classmethod
	def apply_fake_ratio(cls, query):
		logger = logging.getLogger(f"{cls.__module__}.{cls.__qualname__}.apply_fake_ratio")
		mem_id = query["info_hash"].hex()

		if "downloaded" in query:
			query["downloaded"] = 0

		if "left" in query:
			if query["left"] != 0:
				if "left" not in cls.MEMORY[mem_id]:
					cls.MEMORY[mem_id]["left"] = query["left"]
				else:
					query["left"] = cls.MEMORY[mem_id]["left"]

			logger.debug(f"Fake ratio applied, new tracker query:\n{query}")

	def do_GET(self):
		logger = logging.getLogger(f"{type(self).__module__}.{type(self).__qualname__}.do_GET")
		logger.info(f"Request: {self.requestline}")

		try:
			url = self.path
			headers = dict(self.headers)

			if "?" in url:
				path, query_string = url.split("?")
				query = TrackerQuery(query_string)
				logger.debug(f"Traker query:\n{query}")

				self.apply_fake_ratio(query)

				url = f"{path}?{query.build()}"

			response = requests.get(url, headers = headers)
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