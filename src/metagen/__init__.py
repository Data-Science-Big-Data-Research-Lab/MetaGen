"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import sys

DEBUGGING = True


def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if DEBUGGING:
        debug_hook(exception_type, exception, traceback)
    else:
        print(str(exception_type.__name__) + ": " +
              str(exception), file=sys.stderr)


sys.excepthook = exception_handler
