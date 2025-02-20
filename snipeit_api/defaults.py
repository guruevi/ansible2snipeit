DEFAULTS = {
    "status_id_pending": 1,
    "status_id_deployed": 2,
    "manufacturer_id": 1,  # Manufacturers(api=snipe_api).get_by_name("Unknown").id,
    "category_id": 2,  # Category(api=snipe_api).get_by_name("Computers").id,
    "mobile_category_id": 10,  # Category(api=snipe_api).get_by_name("Mobile Devices").id,
    "fieldset_id": 2,  # FieldSets(api=snipe_api).get_by_name("IT").id,
    "mobile_fieldset_id": 4,  # FieldSets(api=snipe_api).get_by_name("Mobile Devices").id,
    "model_id": 1,  # Models(api=snipe_api).get_by_name("Unknown").id,
    "techs": "IT Department",
    "valid_private_mac": ["82B77F", "BC2411"],
    "valid_categories": ["Control", "Process", "Hospital Information System", "Conference Rooms", "Clinical Lab",
                         "Building Management", "Imaging", "Clinical IoT", "Network", "Surgery", "Physical Security",
                         "Communication", "Mobile Devices", "Patient Devices", "General IoT", "Servers", "Computers"],
    "valid_os": ["AlmaLinux", "Android", "Android 6", "Android 7", "APC AOS", "Axis OS", "BSD", "CentOS",
                 "C Executive OS", "ChromeOS 13020.97", "Cisco IOS", "Cisco IOS Software",
                 "Cisco IOS Software [Bengaluru]", "Cisco IOS Software [Cupertino]", "Cisco IOS Software [Denali]",
                 "Cisco IOS Software [Dublin]", "Cisco IOS Software [Everest]", "Cisco IOS Software [Fuji]",
                 "Cisco IOS Software [Gibraltar]", "Cisco IOS XE", "Cisco NX-OS", "CoBos", "CollabOS", "Debian", "DSM",
                 "Embedded Linux", "Embedded Windows 7", "ENEA OSE 4.5.2", "Evolution OS", "Fedora", "Fire OS",
                 "FortiOS", "FreeBSD", "HELiOS", "HP FutureSmart", "HP ProCurve", "iOS", "IOS XE", "JunOS", "Link-OS",
                 "Linux", "Linux Embedded OS", "Linux Embedded RTOS", "Linux Yocto", "macOS", "Mac OS X", "Meraki OS",
                 "OpenVMS", "OS X", "PAN-OS", "Pump OS", "QNX RTOS", "QTS", "RedHat", "Ricoh-OS", "RokuOS",
                 "SonicOS", "SRS", "SUSE", "TC7", "Telium2", "Tizen", "Total Access 924e (2nd Gen),", "tvOS", "Ubuntu",
                 "Uniform-OS", "VxWorks", "watchOS", "webOS", "Windows", "Windows 7", "Windows 7 Enterprise",
                 "Windows 7 Professional", "Windows 7 Ultimate", "Windows 8", "Windows 8.1", "Windows 8.1 Pro",
                 "Windows 10", "Windows 10 Education", "Windows 10 Enterprise", "Windows 10 Enterprise 2015 LTSB",
                 "Windows 10 Enterprise 2016 LTSB", "Windows 10 Enterprise LTSC", "Windows 10 Enterprise N",
                 "Windows 10 IoT Enterprise", "Windows 10 IoT Enterprise LTSC", "Windows 10 Pro",
                 "Windows 10 Pro for Workstations", "Windows 11", "Windows 11 Enterprise",
                 "Windows 11 Enterprise multi-session", "Windows 11 Enterprise N", "Windows 11 Pro",
                 "Windows 11 Pro for Workstations", "Windows 2000", "Windows CE", "Windows Embedded Standard",
                 "Windows Server 2008", "Windows Server 2008 R2 Standard", "Windows Server 2012 R2",
                 "Windows Server 2012 R2 Datacenter", "Windows Server 2012 R2 Standard", "Windows Server 2012 Standard",
                 "Windows Server 2016", "Windows Server 2016 Datacenter", "Windows Server 2016 Standard",
                 "Windows Server 2019", "Windows Server 2019 Datacenter", "Windows Server 2019 Standard",
                 "Windows Server 2022", "Windows Server 2022 Datacenter", "Windows Server 2022 Standard",
                 "Windows Storage Server 2012 R2 Standard", "Windows Storage Server 2012 R2 Workgroup",
                 "Windows Storage Server 2016 Standard", "Windows Storage Server 2016 Workgroup", "Windows XP",
                 "Windows XP 64bit", "Windows XP Professional"],
    "custom_fields": {
        'Storage': {
            'field': '_snipeit_storage_20',
            'value': '',
            'field_format': 'NUMERIC',
            'element': 'text'},
        'OS Version': {
            'field': '_snipeit_os_version_15',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'OS Build': {
            'field': '_snipeit_os_build_16',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'OS Type': {
            'field': '_snipeit_os_type_17',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Internet': {
            'field': '_snipeit_internet_21',
            'value': '',
            'field_format': 'ANY',
            'element': 'radio'},
        'PII': {
            'field': '_snipeit_pii_22',
            'value': '',
            'field_format': 'ANY',
            'element': 'radio'},
        'PHI': {
            'field': '_snipeit_phi_23',
            'value': '',
            'field_format': 'ANY',
            'element': 'checkbox'},
        'EDR': {
            'field': '_snipeit_edr_24',
            'value': '',
            'field_format': 'ANY',
            'element': 'checkbox'},
        'Management': {
            'field': '_snipeit_management_25',
            'value': '',
            'field_format': 'ANY',
            'element': 'checkbox'},
        'CPU': {
            'field': '_snipeit_cpu_18',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'RAM': {
            'field': '_snipeit_ram_19',
            'value': '',
            'field_format': 'NUMERIC',
            'element': 'text'},
        'Operating System': {
            'field': '_snipeit_operating_system_14',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Last User': {
            'field': '_snipeit_last_user_13',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Department': {
            'field': '_snipeit_department_12',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'MAC Address 1': {
            'field': '_snipeit_mac_address_1_1',
            'value': '',
            'field_format': 'MAC',
            'element': 'text'},
        'MAC Address 2': {
            'field': '_snipeit_mac_address_2_2',
            'value': '',
            'field_format': 'MAC',
            'element': 'text'},
        'MAC Address 3': {
            'field': '_snipeit_mac_address_3_3',
            'value': '',
            'field_format': 'MAC',
            'element': 'text'},
        'MAC Address 4': {
            'field': '_snipeit_mac_address_4_4',
            'value': '',
            'field_format': 'MAC',
            'element': 'text'},
        'IP Address': {
            'field': '_snipeit_ip_address_5',
            'value': '',
            'field_format': 'IP',
            'element': 'text'},
        'Switches': {
            'field': '_snipeit_switches_6',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Switch Port': {
            'field': '_snipeit_switch_port_7',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'SSID': {
            'field': '_snipeit_ssid_8',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'VLAN': {
            'field': '_snipeit_vlan_9',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'VLAN Name': {
            'field': '_snipeit_vlan_name_10',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Domain': {
            'field': '_snipeit_domain_11',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Org. Unit': {
            'field': '_snipeit_org_unit_26',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
        'Lab': {
            'field': '_snipeit_lab_27',
            'value': '',
            'field_format': 'ANY',
            'element': 'text'},
    }  # Custom Fields
}
