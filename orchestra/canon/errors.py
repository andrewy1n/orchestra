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


class ReadOnlyStoreError(StoreError):
    pass


class RecordShapeError(StoreError):
    def __init__(self, record_id: str, field: str, message: str) -> None:
        super().__init__(f"record {record_id}: field {field}: {message}")
        self.record_id = record_id
        self.field = field
        self.message = message
