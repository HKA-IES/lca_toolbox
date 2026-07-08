# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
from bw2data.backends import ExchangeDataset, Exchange

# import your own module


def get_exchange(id_: int) -> Exchange:
    """
    Obtain an exchange from its id.

    Adapted from bw2data.utils.get_node().

    Parameters
    ----------
    id_ : int
        ID of the exchange.

    Returns
    -------
    exchange: Exchange
        Exchange.
    """
    # TODO: Implement search by parent and child node?
    qs = ExchangeDataset.select().where(ExchangeDataset.id == id_)

    candidates = [Exchange(obj) for obj in qs]

    if not candidates:
        raise ValueError(f"No exchange with id {id_}")

    return candidates[0]
