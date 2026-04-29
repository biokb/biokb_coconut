import logging
from datetime import date, datetime
from enum import Enum
from typing import Sequence, Type, TypeAlias, Union, get_args, get_origin

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from biokb_coconut.api.schemas import RANGE_PATTERN, NumericOperator, NumericOrRange
from biokb_coconut.db import models

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SASearchResults: TypeAlias = dict[
    str,
    int | Sequence[models.Base] | None,
]


def build_dynamic_query(
    search_obj: BaseModel,
    model_cls: Type[models.Base],
    db: Session,
) -> SASearchResults:
    """
    Build and execute a SQLAlchemy 2.0-style SELECT based on the non-None
    attributes of a Pydantic model instance.  The operator is inferred from
    each field's *declared* type, not the runtime value.
    """
    try:
        filters = create_dynamic_query_filters(search_obj, model_cls)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_102_PROCESSING,
            detail=e,
        )
    stmt = select(model_cls).where(*filters)
    payload = search_obj.model_dump(exclude_none=True, mode="json")

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar()

    limit = payload.get("limit")
    if limit is not None:
        stmt = stmt.limit(limit)
    offset = payload.get("offset")
    if offset is not None:
        stmt = stmt.offset(offset)

    order_by = payload.get("order_by")  # type: ignore
    # check if the order_by field is a valid column of the model
    if order_by is not None and not hasattr(model_cls, order_by):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid 'order_by' field: '{order_by}'. No such column in the model.",
        )
    if order_by is not None:
        stmt = stmt.order_by(order_by)
        order_desc = payload.get("order_desc")  # type: ignore
        if order_desc is not None:
            if isinstance(order_desc, bool) and order_desc:
                stmt = stmt.order_by(getattr(model_cls, order_by).desc())
            else:
                stmt = stmt.order_by(getattr(model_cls, order_by).asc())

    # print the real SQL
    logger.info(
        f"Executing SQL: {stmt.compile(db.bind)} with params: {stmt.compile(db.bind).params}"
    )

    return {
        "count": total_count,
        "limit": limit,
        "offset": offset,
        "results": db.execute(stmt).scalars().all(),
    }


def create_dynamic_query_filters(search_obj, model_cls):
    filters = []

    # Only the attributes the client actually supplied (`exclude_none`)
    field_value_dict = search_obj.model_dump(exclude_none=True, mode="json")

    for field_name, value in field_value_dict.items():
        # Skip operator fields - they're handled when processing their corresponding value fields
        if field_name.endswith("_op") or value is None:
            continue

        # Skip if the SQLAlchemy model has no matching column / hybrid attr
        if not hasattr(model_cls, field_name):
            continue
        column = getattr(model_cls, field_name)

        # The type in the Pydantic model definition
        declared_type = search_obj.__pydantic_fields__[field_name].annotation
        # Handle Optional types (e.g., Optional[str] or Union[str, None])
        if get_origin(declared_type) is Union:
            args = [arg for arg in get_args(declared_type) if arg is not type(None)]
            if args:
                declared_type = args[0]
        origin = get_origin(declared_type) or declared_type

        op_field_name = f"{field_name}_op"
        # STRING ......................................................................
        if origin is str and op_field_name not in field_value_dict:
            filters.append(column.like(value) if ("%" in value) else column == value)
        # NUMBERS .....................................................................
        elif declared_type is NumericOrRange and op_field_name in field_value_dict:
            operator = field_value_dict.get(op_field_name, NumericOperator.EQ.value)
            if isinstance(
                value, str
            ):  # value is only a string if the client sent a range like "10-20" or "10.5 - 20.5"
                found = RANGE_PATTERN.search(
                    value
                )  # This will raise if the format is invalid

                if found:
                    r = found.groupdict()
                    low = float(r["low"]) if r["low_decimal"] else int(r["low"])
                    high = float(r["high"]) if r["high_decimal"] else int(r["high"])
                    value = (low, high)
                    if operator != NumericOperator.BTW.value:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Range value provided for field '{field_name}' but operator is '{operator}'. Expected 'between' operator for range values.",
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid range format for field '{field_name}': '{value}'. Expected format 'min-max'.",
                    )
            # check with resular expression if the value is in the format of "start-end" for between operator
            if operator in (NumericOperator.BTW.value, "between") and isinstance(
                value, tuple
            ):
                filters.append(column.between(value[0], value[1]))
            elif operator == NumericOperator.GT.value:
                filters.append(column > value)
            elif operator == NumericOperator.GTE.value:
                filters.append(column >= value)
            elif operator == NumericOperator.LT.value:
                filters.append(column < value)
            elif operator == NumericOperator.LTE.value:
                filters.append(column <= value)
            else:  # Default to equality
                filters.append(column == value)

        # BOOLEANS ....................................................................
        elif origin is bool:
            filters.append(column.is_(value))

        # DATE / DATETIME – supports equality or simple closed range ...................
        elif origin in (date, datetime):
            if isinstance(value, (list, tuple)) and len(value) == 2:
                filters.append(column.between(value[0], value[1]))
            else:
                filters.append(column == value)

        elif isinstance(origin, type) and issubclass(origin, Enum):
            filters.append(column == value)

        # FALLBACK .....................................................................
        else:
            logger.warning(
                f"Unsupported type for field '{field_name}': {declared_type}. "
                "Using equality operator as fallback."
            )
            filters.append(column == value)

    return filters
