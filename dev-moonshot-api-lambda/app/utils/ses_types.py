from enum import Enum


class SesIdentityStatus(str, Enum):
    Success = 'Success'
    Pending = 'Pending'
    Missing = 'Missing'
    Invalid = 'Invalid'


class MailStatus(str, Enum):
    # SES Built-in Status
    BOUNCE = 'Bounce'
    COMPLAINT = 'Complaint'
    DELIVERY = 'Delivery'
    SEND = 'Send'
    REJECT = 'Reject'
    OPEN = 'Open'
    CLICK = 'Click'
    RENDER_FAILURE = 'Rendering Failure'
    DELIVERY_DELAY = 'DeliveryDelay'
    # Mail Postman Status
    PENDING = 'Pending'
    CANCELLED = 'Cancelled'
    TRIGGER = 'Trigger'
    INVALID = 'Invalid'
    DEAD_LETTER = 'Dead Letter'


MAIL_STATUS_REMARK = {
    # SES Built-in Status
    'Bounce': 'Recipient email server failed to send the email',
    'Complaint': 'Recipient complaint the email as spam',
    'Delivery': 'Delivered to recipient email server',
    'Send': 'Sent by SES',
    'Reject': 'Rejected by SES due to virus',
    'Open': 'Opened by recipient',
    'Click': 'Link(s) clicked by recipient',
    'Rendering Failure': 'SES failed to render email template',
    'DeliveryDelay': 'Email was delayed in delivery',
    # Mail Postman Status
    'Pending': 'Pending to be processed',
    'Cancelled': 'Cancelled by user',
    'Trigger': 'Passed to SES',
    'Invalid': 'Email failed to be processed by SES',
    'Dead Letter': 'Email placed in dead_letter queue',
}

MAIL_STATUS_STAGE = {
    'Pending': 10,
    'Cancelled': 11,
    'Trigger': 12,
    'Invalid': 13,
    'Reject': 21,
    'Rendering Failure': 22,
    'Dead Letter': 23,
    'Send': 31,
    'Delivery': 32,
    'DeliveryDelay': 33,
    'Bounce': 41,
    'Complaint': 42,
    'Open': 43,
    'Click': 44,
}
