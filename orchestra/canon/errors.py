class StoreError(Exception):
    pass


class StaleWriteError(StoreError):
    pass


class StoreNotInitializedError(StoreError):
    pass


class PartialStoreError(StoreError):
    pass


class StoreLockError(StoreError):
    pass
