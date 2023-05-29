import logging

FORMAT = (
    "%(asctime)s|%(filename)s:%(lineno)s:%(funcName)s()<%(levelname)s>:\t%(message)s"
)

logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger()
