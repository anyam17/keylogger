#!/usr/bin/env python
import elogger

events_logger = elogger.Elogger(10, "https://hooks.slack.com/services/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")
events_logger.execute()