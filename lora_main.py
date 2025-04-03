#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: https://github.com/cloudedbats/wurb_lora
# Author: Arnold Andreasson, info@cloudedbats.org
# License: MIT http://opensource.org/licenses/mit

import asyncio
import logging

# import uvicorn
import lora_core
import lora_utils


async def main():
    """ """
    # LoRa logger.
    lora_utils.logger.setup_rotating_log(
        logger_name=lora_core.logger_name,
        logging_dir=lora_core.logging_dir,
        log_name=lora_core.log_file_name,
        debug_log_name=lora_core.debug_log_file_name,
    )
    logger = logging.getLogger(lora_core.logger_name)
    logger.info("")
    logger.info("")
    logger.info("Welcome to CloudedBats WURB-LoRa")
    logger.info("https://github.com/cloudedbats/wurb_lora")
    logger.info("================= ^ö^ ==================")
    logger.info("")

    try:
        # LoRa settings.
        logger.debug("LoRA - main. Startup settings.")
        # await lora_core.lora_settings.startup(settings_dir=lora_core.settings_dir)

        # LoRa core startup.
        logger.debug("LoRA - main. Startup core.")
        await lora_core.lora_manager.startup()
        await asyncio.sleep(0)

        # # API and app config.
        # port = lora_core.config.get("lora_app.port", default="8084")
        # port = int(port)
        # host = lora_core.config.get("lora_app.host", default="0.0.0.0")
        # log_level = lora_core.config.get("lora_app.log_level", default="info")

        # logger.debug("LoRA - main. Uvicorn startup at port: " + str(port) + ".")
        # config = uvicorn.Config(
        #     "lora_api:app", loop="asyncio", host=host, port=port, log_level=log_level
        # )

        # # LoRa API and app startup.
        # server = uvicorn.Server(config)
        # await server.serve()

        # Run LoRa until cancelled.
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass

        # Shutdown actions.
        logger.debug("LoRA - main. Shutdown started.")
        # await lora_core.lora_settings.shutdown()
        await lora_core.lora_manager.shutdown()
        logger.debug("LoRA - main. Shutdown done.")
    except Exception as e:
        message = "LoRA - main. Exception: " + str(e)
        logger.error(message)


if __name__ == "__main__":
    """ """
    asyncio.run(main())
