# ruff: noqa: E722, SIM105


def operation() -> None:
    raise OSError("unavailable")


def silent_failure() -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except Exception:
        pass


def named_error() -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except Exception as error:
        print(error)


def bare_handler() -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except:
        return


def catches_exit() -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except BaseException:
        return


def tuple_handler() -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except (OSError, Exception):
        return


def reports_failure() -> int:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except Exception as error:
        print(error)
        return 2
    return 0


def raises_again() -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except Exception:
        raise
    finally:
        print("finished")


def conditional_failure(required: bool) -> None:
    # ruleid: orchestra.broad-except
    try:
        operation()
    except Exception:
        if required:
            raise
        return


def specific_handler() -> None:
    # ok: orchestra.broad-except
    try:
        operation()
    except OSError:
        return


class ExceptionAdapter(OSError):
    pass


def specific_tuple_handler() -> None:
    # ok: orchestra.broad-except
    try:
        operation()
    except (OSError, ExceptionAdapter):
        return
