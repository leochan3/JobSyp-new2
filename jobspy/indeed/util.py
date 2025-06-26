from jobspy.model import CompensationInterval, JobType, Compensation
from jobspy.util import get_enum_from_job_type
import re
from typing import Optional


def get_job_type(attributes: list) -> list[JobType]:
    """
    Parses the attributes to get list of job types
    :param attributes:
    :return: list of JobType
    """
    job_types: list[JobType] = []
    for attribute in attributes:
        job_type_str = attribute["label"].replace("-", "").replace(" ", "").lower()
        job_type = get_enum_from_job_type(job_type_str)
        if job_type:
            job_types.append(job_type)
    return job_types


def get_compensation(compensation: dict) -> Compensation | None:
    """
    Parses the job to get compensation
    :param compensation:
    :return: compensation object
    """
    if not compensation["baseSalary"] and not compensation["estimated"]:
        return None
    comp = (
        compensation["baseSalary"]
        if compensation["baseSalary"]
        else compensation["estimated"]["baseSalary"]
    )
    if not comp:
        return None
    interval = get_compensation_interval(comp["unitOfWork"])
    if not interval:
        return None
    min_range = comp["range"].get("min")
    max_range = comp["range"].get("max")
    return Compensation(
        interval=interval,
        min_amount=int(min_range) if min_range is not None else None,
        max_amount=int(max_range) if max_range is not None else None,
        currency=(
            compensation["estimated"]["currencyCode"]
            if compensation["estimated"]
            else compensation["currencyCode"]
        ),
    )


def is_job_remote(job: dict, description: str) -> bool:
    """
    Determines if a job is remote based on job attributes and description
    :param job: job dict
    :param description: job description
    :return: True if remote, False otherwise
    """
    if not description:
        return False

    description_lower = description.lower()
    remote_indicators = [
        "remote",
        "work from home",
        "wfh",
        "telecommute",
        "virtual",
        "distributed",
        "anywhere",
        "location independent",
    ]

    return any(indicator in description_lower for indicator in remote_indicators)


def get_compensation_interval(interval: str) -> CompensationInterval:
    interval_mapping = {
        "DAY": "DAILY",
        "YEAR": "YEARLY",
        "HOUR": "HOURLY",
        "WEEK": "WEEKLY",
        "MONTH": "MONTHLY",
    }
    mapped_interval = interval_mapping.get(interval.upper(), None)
    if mapped_interval and mapped_interval in CompensationInterval.__members__:
        return CompensationInterval[mapped_interval]
    else:
        raise ValueError(f"Unsupported interval: {interval}")


def extract_company_id_from_url(company_url: str) -> Optional[str]:
    """
    Extracts Indeed company ID from a company URL
    :param company_url: URL like 'https://www.indeed.com/cmp/Uber' or '/cmp/Uber'
    :return: Company ID string or None if not found
    """
    if not company_url:
        return None
    
    # Pattern to match /cmp/company-name or /cmp/company-name/
    pattern = r'/cmp/([^/?]+)'
    match = re.search(pattern, company_url)
    
    if match:
        return match.group(1)
    
    return None


def get_company_id_from_name(company_name: str, base_url: str = "https://www.indeed.com") -> Optional[str]:
    """
    Attempts to construct a company ID from company name
    Note: This is a heuristic approach and may not work for all companies
    :param company_name: Name of the company
    :param base_url: Indeed base URL
    :return: Company ID string or None
    """
    if not company_name:
        return None
    
    # Convert company name to URL-friendly format
    # Remove special characters and convert spaces to hyphens
    company_id = re.sub(r'[^\w\s-]', '', company_name.lower())
    company_id = re.sub(r'[-\s]+', '-', company_id).strip('-')
    
    # Common company name variations
    variations = {
        'microsoft': 'Microsoft',
        'google': 'Google',
        'apple': 'Apple',
        'amazon': 'Amazon',
        'meta': 'Meta',
        'facebook': 'Meta',  # Facebook is now Meta
        'uber': 'Uber',
        'lyft': 'Lyft',
        'netflix': 'Netflix',
        'tesla': 'Tesla',
        'spacex': 'SpaceX',
        'airbnb': 'Airbnb',
        'salesforce': 'Salesforce',
        'oracle': 'Oracle',
        'intel': 'Intel',
        'nvidia': 'NVIDIA',
        'amd': 'AMD',
        'cisco': 'Cisco',
        'ibm': 'IBM',
        'dell': 'Dell',
        'hp': 'HP',
        'adobe': 'Adobe',
        'autodesk': 'Autodesk',
        'vmware': 'VMware',
        'palantir': 'Palantir',
        'databricks': 'Databricks',
        'snowflake': 'Snowflake',
        'mongodb': 'MongoDB',
        'elastic': 'Elastic',
        'gitlab': 'GitLab',
        'github': 'GitHub',
        'atlassian': 'Atlassian',
        'slack': 'Slack',
        'zoom': 'Zoom',
        'dropbox': 'Dropbox',
        'box': 'Box',
        'twilio': 'Twilio',
        'stripe': 'Stripe',
        'square': 'Square',
        'paypal': 'PayPal',
        'visa': 'Visa',
        'mastercard': 'Mastercard',
        'goldman-sachs': 'Goldman-Sachs',
        'jpmorgan': 'JPMorgan',
        'morgan-stanley': 'Morgan-Stanley',
        'bank-of-america': 'Bank-of-America',
        'wells-fargo': 'Wells-Fargo',
        'chase': 'Chase',
        'american-express': 'American-Express',
        'disney': 'Disney',
        'warner-bros': 'Warner-Bros',
        'paramount': 'Paramount',
        'sony': 'Sony',
        'nintendo': 'Nintendo',
        'ea': 'EA',
        'activision': 'Activision',
        'blizzard': 'Blizzard',
        'riot-games': 'Riot-Games',
        'epic-games': 'Epic-Games',
        'valve': 'Valve',
        'spotify': 'Spotify',
        'pandora': 'Pandora',
        'soundcloud': 'SoundCloud',
        'tidal': 'Tidal',
        'youtube': 'YouTube',
        'tiktok': 'TikTok',
        'snapchat': 'Snapchat',
        'twitter': 'Twitter',
        'linkedin': 'LinkedIn',
        'reddit': 'Reddit',
        'discord': 'Discord',
        'telegram': 'Telegram',
        'whatsapp': 'WhatsApp',
        'signal': 'Signal',
        'microsoft-teams': 'Microsoft-Teams',
        'zoom': 'Zoom',
        'webex': 'Webex',
        'gotomeeting': 'GoToMeeting',
        'bluejeans': 'BlueJeans',
        'ringcentral': 'RingCentral',
        '8x8': '8x8',
        'five9': 'Five9',
        'genesys': 'Genesys',
        'nice': 'NICE',
        'verint': 'Verint',
        'calabrio': 'Calabrio',
        'talkdesk': 'Talkdesk',
        'aivo': 'Aivo',
        'freshdesk': 'Freshdesk',
        'zendesk': 'Zendesk',
        'intercom': 'Intercom',
        'drift': 'Drift',
        'hubspot': 'HubSpot',
        'salesforce': 'Salesforce',
        'pipedrive': 'Pipedrive',
        'zoho': 'Zoho',
        'monday': 'Monday',
        'asana': 'Asana',
        'trello': 'Trello',
        'jira': 'Jira',
        'confluence': 'Confluence',
        'notion': 'Notion',
        'figma': 'Figma',
        'sketch': 'Sketch',
        'invision': 'InVision',
        'marvel': 'Marvel',
        'principle': 'Principle',
        'framer': 'Framer',
        'webflow': 'Webflow',
        'wix': 'Wix',
        'squarespace': 'Squarespace',
        'shopify': 'Shopify',
        'woocommerce': 'WooCommerce',
        'magento': 'Magento',
        'bigcommerce': 'BigCommerce',
        'squarespace': 'Squarespace',
        'wordpress': 'WordPress',
        'drupal': 'Drupal',
        'joomla': 'Joomla',
        'ghost': 'Ghost',
        'medium': 'Medium',
        'substack': 'Substack',
        'mailchimp': 'Mailchimp',
        'constant-contact': 'Constant-Contact',
        'sendgrid': 'SendGrid',
        'mailgun': 'Mailgun',
        'postmark': 'Postmark',
        'customer-io': 'Customer-IO',
        'klaviyo': 'Klaviyo',
        'drip': 'Drip',
        'convertkit': 'ConvertKit',
        'activecampaign': 'ActiveCampaign',
        'infusionsoft': 'Infusionsoft',
        'keap': 'Keap',
        'pipedrive': 'Pipedrive',
        'hubspot': 'HubSpot',
        'salesforce': 'Salesforce',
        'zoho': 'Zoho',
        'freshsales': 'Freshsales',
        'pipedrive': 'Pipedrive',
        'close': 'Close',
        'outreach': 'Outreach',
        'salesloft': 'SalesLoft',
        'gong': 'Gong',
        'chorus': 'Chorus',
        'execvision': 'ExecVision',
        'callrail': 'CallRail',
        'calltracking': 'CallTracking',
        'marchex': 'Marchex',
        'invoca': 'Invoca',
        'dialogtech': 'DialogTech',
        'callminer': 'CallMiner',
        'callrail': 'CallRail',
        'calltracking': 'CallTracking',
        'marchex': 'Marchex',
        'invoca': 'Invoca',
        'dialogtech': 'DialogTech',
        'callminer': 'CallMiner',
    }
    
    # Check if we have a known variation
    if company_id in variations:
        return variations[company_id]
    
    return company_id
