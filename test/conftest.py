"""Shared pytest configuration for the whole suite.

Its presence puts this directory on sys.path, so the modules the tests share --
``utils`` today, fixtures tomorrow -- resolve the same from every subdirectory.
"""
