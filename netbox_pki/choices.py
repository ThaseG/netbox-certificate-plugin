from utilities.choices import ChoiceSet


class CertificateStatusChoices(ChoiceSet):
    """
    Shared status choices for both Certificate and CertificateAuthority.
    """

    key = 'Certificate.status'

    STATUS_AUTOMATIC_REQUESTED = 'automatic-requested'
    STATUS_AUTOMATIC_CSR = 'automatic-csr'
    STATUS_AUTOMATIC_CREATED = 'automatic-created'
    STATUS_MANUAL = 'manual'

    CHOICES = [
        (STATUS_AUTOMATIC_REQUESTED, 'Automatic - Requested', 'blue'),
        (STATUS_AUTOMATIC_CSR, 'Automatic - CSR', 'cyan'),
        (STATUS_AUTOMATIC_CREATED, 'Automatic - Created', 'green'),
        (STATUS_MANUAL, 'Manual', 'gray'),
    ]


class ProtocolTypeChoices(ChoiceSet):
    key = 'Protocol.type'

    TYPE_ACME = 'acme'
    TYPE_SCEP = 'scep'

    CHOICES = [
        (TYPE_ACME, 'ACME', 'blue'),
        (TYPE_SCEP, 'SCEP', 'purple'),
    ]


class AcmeChallengeTypeChoices(ChoiceSet):
    key = 'Protocol.acme_challenge_type'

    CHALLENGE_HTTP01 = 'http-01'
    CHALLENGE_DNS01 = 'dns-01'
    CHALLENGE_TLSALPN01 = 'tls-alpn-01'

    CHOICES = [
        (CHALLENGE_HTTP01, 'HTTP-01'),
        (CHALLENGE_DNS01, 'DNS-01'),
        (CHALLENGE_TLSALPN01, 'TLS-ALPN-01'),
    ]


class ScepEncryptionAlgorithmChoices(ChoiceSet):
    key = 'Protocol.scep_encryption_algorithm'

    ALGORITHM_AES256 = 'aes256'
    ALGORITHM_AES128 = 'aes128'
    ALGORITHM_DES3 = 'des3'

    CHOICES = [
        (ALGORITHM_AES256, 'AES-256'),
        (ALGORITHM_AES128, 'AES-128'),
        (ALGORITHM_DES3, '3DES'),
    ]


class ScepDigestAlgorithmChoices(ChoiceSet):
    key = 'Protocol.scep_digest_algorithm'

    DIGEST_SHA256 = 'sha256'
    DIGEST_SHA384 = 'sha384'
    DIGEST_SHA512 = 'sha512'
    DIGEST_SHA1 = 'sha1'

    CHOICES = [
        (DIGEST_SHA256, 'SHA-256'),
        (DIGEST_SHA384, 'SHA-384'),
        (DIGEST_SHA512, 'SHA-512'),
        (DIGEST_SHA1, 'SHA-1'),
    ]


class ScepRenewalModeChoices(ChoiceSet):
    key = 'Protocol.scep_renewal_mode'

    MODE_RENEWAL = 'renewal'
    MODE_REENROLLMENT = 'reenrollment'

    CHOICES = [
        (MODE_RENEWAL, 'Renewal'),
        (MODE_REENROLLMENT, 'Re-enrollment'),
    ]


class EnvironmentChoices(ChoiceSet):
    key = 'Protocol.environment'

    ENVIRONMENT_PRODUCTION = 'production'
    ENVIRONMENT_STAGING = 'staging'
    ENVIRONMENT_LAB = 'lab'

    CHOICES = [
        (ENVIRONMENT_PRODUCTION, 'Production', 'green'),
        (ENVIRONMENT_STAGING, 'Staging', 'yellow'),
        (ENVIRONMENT_LAB, 'Lab', 'gray'),
    ]


# Duration choices used by Certificate.expiration, CertificateAuthority.expiration and
# CertificateAuthority.default_cert_expiration. Values are mapped to an approximate number of
# days so the plugin can auto-calculate an expiration_date from a created_date + duration.
DURATION_DAYS = {
    '1_month': 30,
    '45_days': 45,
    '80_days': 80,
    '2_months': 60,
    '3_months': 90,
    '200_days': 200,
    '1_year': 365,
    '2_years': 730,
    '3_years': 1095,
    '4_years': 1460,
    '5_years': 1825,
    '6_years': 2190,
    '7_years': 2555,
    '8_years': 2920,
    '9_years': 3285,
    '10_years': 3650,
    '15_years': 5475,
    '20_years': 7300,
}

_DURATION_LABELS = {
    '1_month': '1 month',
    '45_days': '45 days',
    '80_days': '80 days',
    '2_months': '2 months',
    '3_months': '3 months',
    '200_days': '200 days',
    '1_year': '1 year',
    '2_years': '2 years',
    '3_years': '3 years',
    '4_years': '4 years',
    '5_years': '5 years',
    '6_years': '6 years',
    '7_years': '7 years',
    '8_years': '8 years',
    '9_years': '9 years',
    '10_years': '10 years',
    '15_years': '15 years',
    '20_years': '20 years',
}


class CertificateExpirationChoices(ChoiceSet):
    key = 'Certificate.expiration'

    EXPIRATION_AUTOMATIC = 'automatic'

    CHOICES = [
        (value, _DURATION_LABELS[value])
        for value in (
            '1_month',
            '45_days',
            '80_days',
            '2_months',
            '3_months',
            '200_days',
            '1_year',
            '2_years',
            '3_years',
        )
    ] + [
        (EXPIRATION_AUTOMATIC, 'Automatic'),
    ]


class CAExpirationChoices(ChoiceSet):
    key = 'CertificateAuthority.expiration'

    CHOICES = [
        (value, _DURATION_LABELS[value])
        for value in (
            '1_month',
            '45_days',
            '2_months',
            '3_months',
            '200_days',
            '1_year',
            '2_years',
            '3_years',
            '4_years',
            '5_years',
            '6_years',
            '7_years',
            '8_years',
            '9_years',
            '10_years',
            '15_years',
            '20_years',
        )
    ]


class DefaultCertExpirationChoices(ChoiceSet):
    key = 'CertificateAuthority.default_cert_expiration'

    CHOICES = [
        (value, _DURATION_LABELS[value])
        for value in (
            '1_month',
            '45_days',
            '80_days',
            '2_months',
            '3_months',
            '200_days',
            '1_year',
            '2_years',
            '3_years',
        )
    ]
