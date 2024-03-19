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
            'element': 'text'
        },
    },
}
