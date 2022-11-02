# Torratio

**Torratio** is an HTTP proxy which automatically fakes upload/download ratio of __any[^1]__ BitTorrent client.

If you just want to set it up, go to [wiki/Installation][2] for an easy step-by-step guide!


## How does it work ?

**Torratio** works by modifying [HTTP requests sent by your BitTorrent client to every torrent trackers][1]:

```py
def apply_fake_ratio(self, query):
    mem_id = query["info_hash"].hex()

    if "downloaded" in query:
        query["downloaded"] = 0

    if "left" in query:
        if query["left"] != 0:
            if "left" not in self.MEMORY[mem_id]:
                self.MEMORY[mem_id]["left"] = query["left"]
            else:
                query["left"] = self.MEMORY[mem_id]["left"]
```

- The *uploaded* query field is sent as is.
- The *downloaded* query field is set to 0 unconditionally.
- The *left* query field value changes depending the state of the torrent.


### While leeching (downloading) a torrent

If the *left* query field is not 0, the first value received from the client is recorded and sent as is.
For the subsequent requests, and until received value is 0, the recorded value is sent.

This behavior can be seen as a stalled download from the tracker's point of view.


### While seeding (uploading) a torrent

The *left* query field is 0 and sent as is.


## Prerequisites

You will first need a supported version of **Python 3** with **pip**.


## Installation

`python -m pip install https://github.com/FlorianSG/Torratio/archive/refs/heads/main.tar.gz`

See [wiki/Installation][2] for more details about installation.
See [wiki/Setting-Up][3] to configure your torrent client.


## Usage

### As a daemon

`torratio -a 127.0.0.1 -p 9092`

See [wiki/Running_Torratio][4] for more details about how to run **Torratio** daemon.


### As a Python module

```py
import torratio
torratio.daemon(listen_address = "localhost", listen_port = 8090)
```

See [wiki/Python_API][5] for more details about the API.


## Contributing

If you want to improve this software, report a bug, or submit a new feature, go to [wiki/Contributing][6]


## License

This software is licensed under the Open Software License. See [LICENSE.txt][7] for more detail.


## Author and contact

Florian SARRAUTE-GILLY <torratio@florian-sg.fr>

On GitHub: <https://github.com/FlorianSG/Torratio>


[^1]: **Torratio** works with any BitTorrent compatible client which allow to use an HTTP proxy for peer tracker requests, see [wiki/Setting-Up][3] for more details.


[1]: https://wiki.theory.org/BitTorrent_Tracker_Protocol
[2]: https://github.com/FlorianSG/Torratio/wiki/Installation
[3]: https://github.com/FlorianSG/Torratio/wiki/Setting-Up
[4]: https://github.com/FlorianSG/Torratio/wiki/Running_Torratio
[5]: https://github.com/FlorianSG/Torratio/wiki/Python_API
[6]: https://github.com/FlorianSG/Torratio/wiki/Contributing
[7]: https://github.com/FlorianSG/Torratio/blob/main/LICENCE.txt
