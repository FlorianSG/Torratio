#!/usr/bin/env python3

from setuptools import setup

def version():
	with open("torratio/__init__.py") as f:
		for line in f.readlines():
			if line.startswith("__version__"):
				G = {}
				exec(line, G)
				return G["__version__"]

def readme():
	with open("README.md") as f:
		return f.read()

setup(
	name = "torratio",
	version = version(),
	description = "Torrent tracker ratio proxy",
	long_description = readme(),
	long_description_content_type = "text/markdown",
	author = "Florian Sarraute-Gilly",
	author_email = "torratio@florian-sg.fr",
	classifiers = [
		"Topic :: Communications :: File Sharing",
		"Topic :: Internet :: Proxy Servers",
		"Development Status :: 5 - Production/Stable",
		"License :: OSI Approved :: Open Software License 3.0 (OSL-3.0)",
		"Programming Language :: Python :: 3 :: Only",
		"Operating System :: POSIX :: Linux",
		"Environment :: No Input/Output (Daemon)",
	],
	keywords = [
		"bittorrent",
		"deluge",
		"freeleech",
		"proxy",
		"qbittorrent",
		"ratio",
		"seedbox",
		"torrent",
		"tracker",
		"transmission",
		"vuze",
		"µturrent"
	],
	url = "https://github.com/FlorianSG/Torratio",
	packages = [
		"torratio",
	],
	scripts = [
		"bin/torratio",
	],
	install_requires=[
		"requests",
	],
	license = "Open Software License 3.0 (OSL-3.0)",
	zip_safe = False,
)