from typing import Callable, Any, Optional, Tuple, Dict, Awaitable, Union

from starlette.requests import Request
from starlette.responses import Response


class CustomKeyBuilder:
    def __call__(
        self,
        __function: Callable[..., Any],
        __namespace: str = '',
        *,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[str], str]:


        # Creating key parts
        key_parts = [__namespace]

        # Adding arguments (positional)
        key_parts.extend(str(arg) for arg in args[:2] if arg is not None)
        return ":".join(key_parts)


# An instance of the class that we will pass to the key_builder.
custom_key_builder = CustomKeyBuilder()