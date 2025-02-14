#!/usr/bin/env python
"""Command line interface of financeager application."""
from datetime import datetime
import argparse
import os
import sys

from financeager import offline, __version__, PERIOD_DATE_FORMAT,\
    init_logger, make_log_stream_handler_verbose, setup_log_file_handler
import financeager
from .communication import Client
from .config import Configuration
from .entries import CategoryEntry
from .exceptions import OfflineRecoveryError, InvalidConfigError,\
    PreprocessingError

logger = init_logger(__name__)

# Exit codes
SUCCESS = 0
FAILURE = 1


def main():
    """Main command line entry point of the application. The config and the log
    directory are created. A FileHandler is added to the package logger.
    All command line arguments and options are parsed and passed to 'run()'.
    """
    os.makedirs(financeager.DATA_DIR, exist_ok=True)

    # Adding the FileHandler here avoids cluttering the log during tests
    setup_log_file_handler()

    # Most runs return None which evaluates to return code 0
    sys.exit(run(**_parse_command()))


def run(command=None, config_filepath=None, verbose=False, **params):
    """High-level API entry point.
    All 'params' are passed to 'Client.safely_run()'.
    'config_filepath' specifies the path to a custom config file (optional). If
    'verbose' is set, debug level log messages are printed to the terminal.

    This function can be used for scripting. Provide 'command' and 'params'
    according to what the command line interface accepts (consult help via
    `financeager [command] --help`), e.g. {"command": "add", "name":
    "champagne", "value": "99"}.

    :return: UNIX return code (zero for success, non-zero otherwise)
    """
    if verbose:
        make_log_stream_handler_verbose()

    exit_code = FAILURE

    if config_filepath is None and os.path.exists(financeager.CONFIG_FILEPATH):
        config_filepath = financeager.CONFIG_FILEPATH
    try:
        configuration = Configuration(filepath=config_filepath)
    except InvalidConfigError as e:
        logger.error("Invalid configuration: {}".format(e))
        return FAILURE

    date_format = configuration.get_option("FRONTEND", "date_format")
    try:
        _preprocess(params, date_format)
    except PreprocessingError as e:
        logger.error(e)
        return FAILURE

    service_name = configuration.get_option("SERVICE", "name")
    if service_name == "flask":
        init_logger("urllib3")

    client = Client(
        configuration=configuration, out=Client.Out(logger.info, logger.error))
    success, store_offline = client.safely_run(command, **params)

    if success:
        exit_code = SUCCESS

        # When regular command was successfully executed, attempt to recover
        # offline backup
        try:
            if offline.recover(client):
                logger.info("Recovered offline backup.")
        except OfflineRecoveryError:
            logger.error("Offline backup recovery failed!")
            exit_code = FAILURE

    if store_offline and offline.add(command, **params):
        logger.info("Stored '{}' request in offline backup.".format(command))

    if service_name == "none":
        client.run("stop")

    return exit_code


def _preprocess(data, date_format=None):
    """Preprocess data to be passed to Client (e.g. convert date format, parse
    'filters' options passed with print command).

    :raises: PreprocessError if preprocessing failed.
    """
    date = data.get("date")
    # recovering offline data does not bring any date format because the data
    # has already been converted
    if date is not None and date_format is not None:
        try:
            date = datetime.strptime(date,
                                     date_format).strftime(PERIOD_DATE_FORMAT)
            data["date"] = date
        except ValueError:
            raise PreprocessingError("Invalid date format.")

    filter_items = data.get("filters")
    if filter_items is not None:
        # convert list of "key=value" strings into dictionary
        parsed_items = {}
        try:
            for item in filter_items:
                key, value = item.split("=")
                parsed_items[key] = value.lower()

            try:
                # Substitute category default name
                if parsed_items["category"] == CategoryEntry.DEFAULT_NAME:
                    parsed_items["category"] = None
            except KeyError:
                # No 'category' field present
                pass

            data["filters"] = parsed_items
        except ValueError:
            # splitting returned less than two parts due to missing separator
            raise PreprocessingError("Invalid filter format: {}".format(item))


def _parse_command(args=None):
    """Parse the given list of args and return the result as dict."""

    parser = argparse.ArgumentParser(
        description="An application (possibly running as Flask webservice) "
        "that helps you administering your daily expenses and earnings.")

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="financeager version {}".format(__version__),
        help="display version info and exit")  # pragma: no cover

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="command",
        help="list of available subcommands")

    add_parser = subparsers.add_parser(
        "add", help="add an entry to the database")

    add_parser.add_argument("name", help="entry name")
    add_parser.add_argument("value", type=float, help="entry value")
    add_parser.add_argument(
        "-c", "--category", default=None, help="entry category")
    add_parser.add_argument("-d", "--date", default=None, help="entry date")

    add_parser.add_argument(
        "-t",
        "--table-name",
        default=None,
        help="""table to add the entry to. With 'recurrent', specify at
least a frequency, start date and end date are optional. Default:
'standard'""")
    add_parser.add_argument(
        "-f",
        "--frequency",
        help="frequency of recurrent "
        "entry; one of yearly, half-yearly, quarterly, monthly, weekly, "
        "daily.")
    add_parser.add_argument(
        "-s", "--start", default=None, help="start date of recurrent entry")
    add_parser.add_argument(
        "-e", "--end", default=None, help="end date of recurrent entry")

    get_parser = subparsers.add_parser(
        "get", help="show information about single entry")
    get_parser.add_argument("eid", help="entry ID")
    get_parser.add_argument(
        "-t",
        "--table-name",
        default=None,
        help="Table to get the entry from. Default: 'standard'.")

    rm_parser = subparsers.add_parser(
        "rm", help="remove an entry from the database")
    rm_parser.add_argument("eid", help="entry ID")
    rm_parser.add_argument(
        "-t",
        "--table-name",
        default=None,
        help="Table to remove the entry from. Default: 'standard'.")

    update_parser = subparsers.add_parser(
        "update", help="update one or more fields of an database entry")
    update_parser.add_argument("eid", type=int, help="entry ID")
    update_parser.add_argument(
        "-t",
        "--table-name",
        help="Table containing the entry. Default: 'standard'")
    update_parser.add_argument("-n", "--name", help="new name")
    update_parser.add_argument("-v", "--value", type=float, help="new value")
    update_parser.add_argument("-c", "--category", help="new category")
    update_parser.add_argument(
        "-d", "--date", help="new date (for standard entries only)")
    update_parser.add_argument(
        "-f", "--frequency", help="new frequency (for recurrent entries only)")
    update_parser.add_argument(
        "-s", "--start", help="new start date (for recurrent entries only)")
    update_parser.add_argument(
        "-e", "--end", help="new end date (for recurrent entries only)")

    copy_parser = subparsers.add_parser(
        "copy", help="copy an entry from one period to another")
    copy_parser.add_argument("eid", help="entry ID")
    copy_parser.add_argument(
        "-s",
        "--source",
        default=None,
        dest="source_period",
        help="period to copy the entry from")
    copy_parser.add_argument(
        "-d",
        "--destination",
        default=None,
        dest="destination_period",
        help="period to copy the entry to")
    copy_parser.add_argument(
        "-t",
        "--table-name",
        default=None,
        help="Table to copy the entry from/to. Default: 'standard'.")

    list_parser = subparsers.add_parser(
        "list", help="list all entries in the period database")
    list_parser.add_argument(
        "-f",
        "--filters",
        default=None,
        nargs="+",
        help="filter for name, "
        "date and/or category substring, e.g. name=beer category=groceries")
    list_parser.add_argument(
        "-s",
        "--stacked-layout",
        action="store_true",
        help="if true, display earnings and expenses in stacked layout, "
        "otherwise side-by-side")
    list_parser.add_argument(
        "--entry-sort",
        choices=["name", "value", "date", "eid"],
        default=financeager.DEFAULT_BASE_ENTRY_SORT_KEY)
    list_parser.add_argument(
        "--category-sort",
        choices=["name", "value"],
        default=financeager.DEFAULT_CATEGORY_ENTRY_SORT_KEY)

    periods_parser = subparsers.add_parser(
        "periods", help="list all period databases")

    service_parser = subparsers.add_parser(
        "service", help="interact with the webservice")

    # Add common options to subparsers
    for subparser in subparsers.choices.values():
        subparser.add_argument(
            "-C",
            "--config-filepath",
            help="path to config file. Default: {}".format(
                financeager.CONFIG_FILEPATH))
        subparser.add_argument(
            "--verbose",
            action="store_true",
            help="Be verbose about internal workings")

        if subparser not in [periods_parser, copy_parser, service_parser]:
            subparser.add_argument(
                "-p", "--period", help="name of period to modify or query")

    return vars(parser.parse_args(args=args))


if __name__ == "__main__":
    main()
