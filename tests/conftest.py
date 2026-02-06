"""pytest 設定

pytest-asyncio と playwright の競合を回避するための設定です。
"""


def pytest_configure(config):
    """pytest 設定

    asyncio_mode が 'auto' の場合、playwright と競合する可能性があります。
    ここでは、特別な設定は行いません。
    """
    pass
