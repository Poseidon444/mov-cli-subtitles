##from __future__ import annotations
##from typing import TYPE_CHECKING
##
##if TYPE_CHECKING:
##    from ..media import Media
##    from ..config import Config
##
##import subprocess
##from devgoldyutils import Colours
##
##from .. import errors
##from .player import Player
##
##__all__ = ("VLC",)
##
##class VLC(Player):
##    def __init__(self, config: Config) -> None:
##        super().__init__(Colours.ORANGE.apply("VLC"), config)
##
##    def play(self, media: Media) -> subprocess.Popen:
##        """Plays this media in the VLC media player."""
##
##        self.logger.info("Launching VLC Media Player...")
##
##        if self.platform == "Linux" or self.platform == "Windows":
##            try:
##                return subprocess.Popen(
##                    [
##                        "vlc",
##                        # f'--sub-file={media.subtitles}', # some way to add subs!! TODO
##                        f'--http-referrer="{media.referrer}"', 
##                        f'--meta-title="{media.display_name}"', 
##                        media.url
##                    ]
##                )
##
##            except ModuleNotFoundError:
##                raise errors.PlayerNotFound(self)
##
##        raise errors.PlayerNotSupported(self, self.platform)


import re
import tempfile
import uuid
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from ..media import Media
    from .. import Config
    from ..utils.platform import SUPPORTED_PLATFORMS

import subprocess
from devgoldyutils import Colours, LoggerAdapter

from .. import errors
from .. import http_client
from ..logger import mov_cli_logger
from .player import Player

__all__ = ("VLC",)

http_match = r"^(http|https)://([\w\.-]+)\.([a-z]{2,6})(:\d+)?(/[\w\.-]*)?$"

logger = LoggerAdapter(mov_cli_logger, prefix = Colours.ORANGE.apply("VLC"))

class VLC(Player):
    def __init__(self, platform: SUPPORTED_PLATFORMS, config: Config, **kwargs) -> None:
        self.platform = platform
        self.config = config

        super().__init__(**kwargs)

    def play(self, media: Media) -> Optional[subprocess.Popen]:
        """Plays this media in the VLC media player."""

        logger.info("Launching VLC Media Player...")

        if self.platform == "Android":
            return subprocess.Popen(
                [
                    "am",
                    "start",
                    "-n",
                    "org.videolan.vlc/org.videolan.vlc.gui.video.VideoPlayerActivity",
                    "-e",
                    "title",
                    media.display_name,
                    media.url,
                ]
            )

        elif self.platform == "iOS":
            logger.debug("Detected your using iOS. \r\n")

            with open('/dev/clipboard', 'w') as f:
                f.write(f"vlc://{media.url}")

            logger.info("The URL was copied into your clipboard. To play it, open a browser and paste the URL.")

            return None

        elif self.platform == "Linux" or self.platform == "Windows":
            try:
                args = [
                    "vlc", 
                    f'--meta-title="{media.display_name}"', 
                    media.url, 
                    "--quiet"
                ]

                if media.referrer is not None:
                    args.append(f'--http-referrer="{media.referrer}"')

                if media.audio_url is not None:
                    args.append(f"--input-slave={media.audio_url}") # WHY IS THIS UNDOCUMENTED!!!

                if media.subtitles is not None:
                    subtitles = media.subtitles

                    if re.match(http_match ,media.subtitles):
                        temp_dir = tempfile.gettempdir() + r'\mov-cli'
                        response = http_client.HTTPClient.get(url = media.subtitles)
                        z = str(uuid.uuid4())
                        with open(f"{temp_dir}/{z}", 'wb') as sub_file:
                            sub_file.write(response.content)
                        # TODO: If it's a url download the subtitles 
                        # to a temporary directory then give the path to vlc.


                    args.append(f"--sub-file={temp_dir}/{z}")

                if self.config.resolution:
                    args.append(f"--adaptive-maxwidth={self.config.resolution}") # NOTE: I don't really know if that works ~ Ananas

                return subprocess.Popen(args)

            except (ModuleNotFoundError, FileNotFoundError):
                raise errors.PlayerNotFound(self)

        return None