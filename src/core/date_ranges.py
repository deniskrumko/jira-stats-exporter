from calendar import month_name, monthrange
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel


class DateRange(BaseModel):
    """Inclusive date range."""

    start: date
    end: date
    info: str | None = None

    def __str__(self) -> str:
        """Return the formatted date range."""
        result = f"{self.start.isoformat()} – {self.end.isoformat()}"
        if self.info:
            result += f" ({self.info})"
        return result

    @property
    def colored_string(self) -> str:
        result = f"[yellow not b]{self.start.isoformat()} – {self.end.isoformat()}[/]"
        if self.info:
            result += f" [dim]({self.info})[/dim]"
        return result

    @property
    def days(self) -> int:
        """Return the number of days in the date range."""
        return (self.end - self.start).days + 1

    @classmethod
    def resolve(
        cls,
        *,
        week: int | None = None,
        quarter: int | None = None,
        month: int | None = None,
        day: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        year: int | None = None,
        **kwargs: Any,  # noqa
    ) -> "DateRange":
        """Resolve CLI date options into an inclusive date range."""
        selected = [
            week is not None,
            quarter is not None,
            month is not None,
            day is not None,
            from_date is not None or to_date is not None,
        ]
        if sum(selected) != 1:
            raise ValueError(
                "Specify exactly one date range option: "
                "week, quarter, month, day, or from_date/to_date",
            )

        today = date.today()
        target_year = year or today.year

        if week is not None:
            return cls._resolve_week(week, target_year, today)
        if quarter is not None:
            return cls._resolve_quarter(quarter, target_year, today)
        if month is not None:
            return cls._resolve_month(month, target_year, today)
        if day is not None:
            return cls._resolve_day(day, target_year, today)

        return cls._resolve_explicit_range(from_date, to_date)

    @staticmethod
    def _resolve_week(value: int, year: int, today: date) -> "DateRange":
        """Resolve a week option into an inclusive date range."""
        if value == 0:
            current_week_start = today - timedelta(days=today.weekday())
            return DateRange(
                start=current_week_start,
                end=today,
                info="Current week",
            )

        if value <= 0:
            current_week_start = today - timedelta(days=today.weekday())
            start = current_week_start + timedelta(weeks=value)
            return DateRange(
                start=start,
                end=start + timedelta(days=6),
                info=f"Week {value}",
            )

        try:
            start = date.fromisocalendar(year, value, 1)
        except ValueError as error:
            raise ValueError(f"Invalid ISO week for year {year}: {value}") from error

        return DateRange(
            start=start,
            end=start + timedelta(days=6),
            info=f"Week {value}",
        )

    @staticmethod
    def _resolve_quarter(value: int, year: int, today: date) -> "DateRange":
        """Resolve a quarter option into an inclusive date range."""
        if value == 0:
            current_quarter = (today.month - 1) // 3 + 1
            return DateRange(
                start=DateRange._quarter_range(today.year, current_quarter).start,
                end=today,
                info="Current quarter",
            )

        if value <= 0:
            current_quarter = (today.month - 1) // 3
            quarter_index = today.year * 4 + current_quarter + value
            target_year = quarter_index // 4
            target_quarter = quarter_index % 4 + 1
            return DateRange._quarter_range(target_year, target_quarter)

        if value > 4:
            raise ValueError("--quarter must be between 1 and 4")
        return DateRange._quarter_range(year, value)

    @staticmethod
    def _resolve_month(value: int, year: int, today: date) -> "DateRange":
        """Resolve a month option into an inclusive date range."""
        if value == 0:
            return DateRange(
                start=date(today.year, today.month, 1),
                end=today,
                info=f"{month_name[today.month]}, {today.year}",
            )

        if value <= 0:
            month_index = today.year * 12 + today.month - 1 + value
            target_year = month_index // 12
            target_month = month_index % 12 + 1
            return DateRange._month_range(target_year, target_month)

        if value > 12:
            raise ValueError("--month must be between 1 and 12")
        return DateRange._month_range(year, value)

    @staticmethod
    def _resolve_day(value: int, year: int, today: date) -> "DateRange":
        """Resolve a day option into an inclusive date range."""
        if value <= 0:
            target = today + timedelta(days=value)
            return DateRange(start=target, end=target)

        try:
            target = date(year, 1, 1) + timedelta(days=value - 1)
        except OverflowError as error:
            raise ValueError(f"Invalid day for year {year}: {value}") from error
        if target.year != year:
            raise ValueError(f"Invalid day for year {year}: {value}")
        return DateRange(start=target, end=target)

    @staticmethod
    def _resolve_explicit_range(from_date: str | None, to_date: str | None) -> "DateRange":
        """Resolve explicit date strings into an inclusive date range."""
        if from_date is None or to_date is None:
            raise ValueError("--from and --to must be specified together")

        start = DateRange._parse_date(from_date, "--from")
        end = DateRange._parse_date(to_date, "--to")
        if start > end:
            raise ValueError("--from cannot be later than --to")
        return DateRange(start=start, end=end)

    @staticmethod
    def _month_range(year: int, month: int) -> "DateRange":
        """Return the inclusive date range for a calendar month."""
        return DateRange(
            start=date(year, month, 1),
            end=date(year, month, monthrange(year, month)[1]),
            info=f"{month_name[month]}, {year}",
        )

    @staticmethod
    def _quarter_range(year: int, quarter: int) -> "DateRange":
        """Return the inclusive date range for a calendar quarter."""
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        return DateRange(
            start=date(year, start_month, 1),
            end=date(year, end_month, monthrange(year, end_month)[1]),
            info=f"{year} Q{quarter}",
        )

    @staticmethod
    def _parse_date(value: str, option_name: str) -> date:
        """Parse a CLI date option value."""
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f"{option_name} must be in YYYY-MM-DD format") from error
