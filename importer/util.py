import re
from typing import Mapping, Union, TypeVar, MutableMapping

V = TypeVar(str, bool, int)


def de_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def m(mapping: Mapping,
      name: str,
      field_type: V,
      default: Union[None, V] = None) -> Union[None, V]:
    """
    Coerce an element in a mapping by type and key
    :param mapping: The mapping
    :param name: The name of the key
    :param field_type: The type expected
    :param default: The default value, should the retrieved value be none
    :return: The value of the type specified in 't' or None
    """
    # Check to see if its present
    if name not in mapping:
        return default

    # Get the value
    ret = mapping[name]

    # Try to avoid storing black strings or whitespace at all costs
    if field_type is str:
        ret = str(ret).strip()
        return ret if ret else default

    # Coerce the final value
    return None if ret is '' else field_type(ret)


def mutate(mapping: MutableMapping, name: str, field_type: V) -> None:
    """
    Mutate a mapping by coercing a value in the map to another type
    :param mapping: The map
    :param name: The name of the value
    :param field_type: The type
    """
    if name in mapping:
        mapping[name] = m(mapping, name, field_type)
