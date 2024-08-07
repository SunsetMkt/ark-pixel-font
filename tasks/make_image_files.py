import logging

import configs
from services import image_service

logging.basicConfig(level=logging.DEBUG)


def main():
    for font_config in configs.font_configs:
        image_service.make_preview_image_file(font_config)
    image_service.make_readme_banner()
    image_service.make_github_banner()
    image_service.make_itch_io_banner()
    image_service.make_itch_io_background()
    image_service.make_itch_io_cover()
    image_service.make_afdian_cover()


if __name__ == '__main__':
    main()
