#!/usr/bin/env python3
"""
Run script for FastAPI USB PD Parser
"""
from usbpd.app_runner import USBPDParserApp

if __name__ == "__main__":
	raise SystemExit(USBPDParserApp.main())
