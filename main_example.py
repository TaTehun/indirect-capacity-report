import logging
import sys
from datetime import datetime
from pathlib import Path

from processors import air_processor, otr_processor, vessel_processor
from processors.report_builder import write as write_report
from email_pipeline import email_setup as cfg
from email_pipeline.sender import load_sender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

TEMPLATE = cfg.CAPACITY_DIR / 'Inbound Capacity Report.xlsx'


def find_tracking_file(search_dir: Path, keyword: str, today: datetime) -> Path:
    date_str = today.strftime('%m-%d-%y')
    matches = list(search_dir.glob(f'*{date_str}*{keyword}*.xlsm'))
    if not matches:
        raise FileNotFoundError(f'*{date_str}*{keyword}*.xlsm')
    return matches[0]


def build_output_path(today: datetime) -> Path:
    week_num = int(today.isocalendar().week)
    return cfg.CAPACITY_DIR / f'Inbound Capacity Report WK{week_num:02d}.xlsx'


def send_failure_alert(sender, week_num: int, error_msg, missing_file: bool = False):
    subject = cfg.EMAIL_SUBJECT_FAILURE.format(week_num)
    if missing_file:
        items = error_msg if isinstance(error_msg, list) else [error_msg]
        lines = ''.join(f'&bull; {m}<br>' for m in items)
        detail = (
            f'<b>Missing File(s):</b><br>{lines}<br>'
            'Please ensure all tracking files exist in the correct folders and re-run.'
        )
    else:
        detail = f'<b>Unexpected Error:</b> {error_msg}'
    body = (
        '<BODY style="font-size:11pt;font-family:Calibri">'
        f'Inbound Capacity Report WK{week_num:02d} failed.<br><br>'
        f'{detail}'
        '</BODY>'
    )
    sender.send(subject=subject, body=body, to=cfg.EMAIL_TO_FAILURE, cc=cfg.EMAIL_CC_FAILURE)


def main():
    today    = datetime.today()
    week_num = int(today.isocalendar().week)
    log.info(f'Starting Inbound Capacity Report — {today.strftime("%Y-%m-%d")}')

    sender = load_sender()

    try:
        missing = []
        file_specs = [
            (cfg.AIR_DIR,   'Air Inbound Tracking',    'AIR'),
            (cfg.OTR_DIR,   'OTR Inbound Tracking',    'OTR'),
            (cfg.OCEAN_DIR, 'Vessel Inbound Tracking', 'Vessel'),
        ]
        found = {}
        for search_dir, keyword, label in file_specs:
            try:
                found[label] = find_tracking_file(search_dir, keyword, today)
                log.info(f'{label}: {found[label].name}')
            except FileNotFoundError as e:
                log.error(str(e))
                missing.append(str(e))

        if missing:
            if sender:
                send_failure_alert(sender, week_num, missing, missing_file=True)
            return

        air_data    = air_processor.process(found['AIR'],    today)
        otr_data    = otr_processor.process(found['OTR'],    today)
        vessel_data = vessel_processor.process(found['Vessel'], today)

        output_path = build_output_path(today)
        log.info(f'Writing report → {output_path.name}')
        write_report(TEMPLATE, output_path, air_data, otr_data, vessel_data, today)
        log.info('Report written successfully.')

    except Exception as e:
        log.error(f'Unexpected error: {e}')
        if sender:
            send_failure_alert(sender, week_num, str(e), missing_file=False)
        return

    if sender is None:
        log.error('Email sender unavailable — report saved locally only.')
        return

    subject = cfg.EMAIL_SUBJECT.format(week_num)
    body = (
        '<BODY style="font-size:11pt;font-family:Calibri">'
        f'Please see attached Inbound Capacity Report for WK{week_num:02d}.'
        '</BODY>'
    )
    ok = sender.send(
        subject    = subject,
        body       = body,
        to         = cfg.EMAIL_TO,
        cc         = cfg.EMAIL_CC,
        bcc        = cfg.EMAIL_BCC,
        attachment = output_path,
    )
    if ok:
        log.info(f'Report emailed to {cfg.EMAIL_TO}')
    else:
        log.error('Failed to send email.')


if __name__ == '__main__':
    main()
