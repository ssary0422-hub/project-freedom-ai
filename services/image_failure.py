"""Owner-visible diagnostics without provider messages, credentials or file paths."""
import re
import traceback
from pathlib import Path
from flask import current_app, session


def record_image_failure(error):
    chain = []
    cause = error
    while cause is not None and len(chain) < 4:
        code = getattr(cause, 'code', None)
        chain.append({
            'type': type(cause).__name__,
            'status': getattr(cause, 'status_code', None),
            'code': code if isinstance(code, str) and re.fullmatch(r'[a-zA-Z0-9_]{1,80}', code) else None,
        })
        cause = cause.__cause__
    frames = [{'module': Path(frame.filename).name, 'function': frame.name, 'line': frame.lineno}
              for frame in traceback.extract_tb(error.__traceback__)[-6:]]
    session['sns_image_failure'] = {'chain': chain, 'frames': frames}
    current_app.logger.exception('SNS image generation failed')
