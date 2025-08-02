from __future__ import annotations

import html
import re
from dataclasses import dataclass, field, fields
from typing_extensions import Self

from dataclasses_json import dataclass_json, config

from .api import SnipeITApi, logging
from .defaults import DEFAULTS
from .helpers import clean_mac, clean_tag, clean_manufacturer, clean_user, filter_list, parse_isoformat


def exclude_ifempty(value):
    return not value


def exclude_always(_):
    return True


@dataclass
class CustomField:
    field: str
    value: str
    field_format: str
    element: str


@dataclass
class Actions:
    update: bool = False
    delete: bool = False
    restore: bool = False
    clone: bool = False
    checkout: bool = False
    checkin: bool = False
    bulk_selectable: bool = False

@dataclass_json
@dataclass
class SnipeObject:
    api: SnipeITApi | None = field(metadata=config(exclude=exclude_always), default=None)
    id: int = 0
    name: str = ""
    _curr_data: dict = field(metadata=config(exclude=exclude_always), default_factory=dict)
    _populated_from_api: bool = False

    def __post_init__(self):
        if self.api and self.id:
            self.get_by_id()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def to_patch_dict(self, curr_data) -> dict:
        for k, v in self._curr_data.items():
            if (k in curr_data and k != 'id' and
                    (curr_data[k] == v or
                     (isinstance(curr_data[k], str) and html.unescape(curr_data[k]) == html.unescape(v))
                    )
            ):
                del curr_data[k]
        return curr_data

    def upsert(self, method='PATCH'):
        if not self.id:
            return self.create()

        curr_data = self.to_dict()
        # If method is PATCH, we only want to update the fields that have changed
        if method == 'PATCH':
            curr_data = self.to_patch_dict(curr_data)

        if not curr_data:
            logging.debug("No changes to save")
            return self

        logging.debug(f"Updating {self.__class__.__name__} with ID {self.id}, data: {curr_data}")
        data = self.api.call(f"{self.__class__.__name__}/{self.id}".lower(), method=method, payload=curr_data)
        if "status" in data and data['status'] == "success" and "payload" in data and data['payload']:
            return self.populate(data['payload'], from_api=True)
        logging.debug(curr_data)
        raise ValueError(f"Failed to update {self.__class__.__name__}, {data}")

    def create(self, extra_data=None) -> Self:
        if not extra_data:
            extra_data = {}
        if self.id:
            logging.debug(f"Object already exists {self.__class__.__name__.lower()} - {self.id}")
            return self
        payload = self.to_dict() | extra_data
        data = self.api.call(f"{self.__class__.__name__.lower()}", method="POST", payload=payload)
        if data['status'] == "success" and data['payload']:
            return self.populate(data['payload'], from_api=True)

        raise ValueError(f"Failed to create {self.__class__.__name__}, {data}, {payload}")

    def get_by_id(self, db_id: int = 0):
        # Connect to the Snipe-IT API and fetch the object
        db_id = db_id or self.id
        if not db_id:
            raise ValueError("ID not set, object has not been created in database (yet)")
        if self.id and self._populated_from_api:
            logging.debug(f"Already populated, no need to fetch {self.__class__.__name__} with ID {db_id}")
            return self

        data = self.api.call(f"{self.__class__.__name__.lower()}/{db_id}")
        if data and 'id' in data:
            return self.populate(data, from_api=True)

        logging.error(f"Failed to fetch {self.__class__.__name__} with ID {db_id}, {data}")
        return self

    def get_by_name(self, name: str = ""):
        # Connect to the Snipe-IT API and fetch the object
        name = name or self.name
        name.replace("&amp;", "and").replace("&", "and")  # Snipe-IT cannot search for & in names
        if not name:
            name = "Unknown"

        return self.search(f"{self.__class__.__name__.lower()}", payload={"name": name})

    def search(self, endpoint, payload=None, method='GET'):
        if not self.api:
            raise ValueError("API not set")
        if self.id:
            logging.debug(f"Already have an ID for {endpoint} no need to search")
            return self
        data = self.api.call(endpoint, payload=payload, method=method)
        if 'total' in data:
            if data['total'] > 1:
                logging.warning(f"More than one result found for {endpoint}, using the first one.")
            if data['total'] > 0:
                return self.populate(data['rows'][0], from_api=True)
        logging.debug(f"No results found for {endpoint} {payload or ''}")
        return self

    def populate(self, data: dict, from_api=False) -> Self:
        for k, v in data.items():
            if isinstance(v, str):
                v = html.unescape(v)
            setattr(self, k, v)
        self._populated_from_api = from_api
        return self

    def store_state(self):
        setattr(self, '_curr_data', self.to_dict())
        return self

    def __setattr__(self, key, value):
        dcfields: tuple = fields(self)
        if key == 'status_label':
            key = 'status'

        if '_id' in key:
            # Make sure to cast as int, the API returns strings
            value: int = int(value or 0)
            if value > 0:
                obj = getattr(self, key.replace('_id', ''), None)
                if isinstance(obj, SnipeObject) and not obj.id:
                    obj.id = value
                    obj.api = self.api
                    obj.get_by_id()

        if dcfield := [f for f in dcfields if f.name == key]:
            ftype = dcfield[0].type.split(' | ')[0]
            if ftype == 'float' or ftype == 'int':
                if type(value) is str:
                    value = value.replace(",", "").replace("$", "")
                value: float = float(value or 0)
                if ftype == 'int':
                    value: int = int(value)
            elif ftype.startswith('list') and ftype[5:-1] not in ['str', 'int', 'float', 'bool', 'dict',
                                                                  'list']:
                # Iterate over the list and coerce to the correct type
                if 'rows' in value and 'total' in value:
                    value: list = [globals()[ftype[5:-1]](api=self.api, **v) for v in value['rows']]
                else:
                    value: list = [globals()[ftype[5:-1]](api=self.api, **v) for v in value]
            elif type(value) is dict and 'dict' not in ftype:
                if 'id' in value:
                    setattr(self, key + '_id', value['id'])
                    return
                    # if ftype != self.__class__.__name__ and 'id' in self[key] and self[key].id != value['id']:
                    #    value: SnipeObject = globals()[ftype](api=self.api, **value)
                elif 'datetime' in value:
                    value = value['datetime']
                elif 'date' in value:
                    value = value['date']
                elif ftype == 'Actions':
                    value: Actions = Actions(**value)
                elif ftype != self.__class__.__name__:
                    value = globals()[ftype](api=self.api, **value)

        super().__setattr__(key, value)


def list_to_id(objects: list):
    return [obj.id for obj in objects]


@dataclass_json
@dataclass
class SnipeDataObject(SnipeObject):
    available_actions: Actions = field(metadata=config(exclude=exclude_always), default_factory=Actions)
    created_at: str = field(metadata=config(exclude=exclude_always), default="")
    updated_at: str = field(metadata=config(exclude=exclude_always), default="")
    deleted_at: str | None = field(metadata=config(exclude=exclude_always), default=None)


@dataclass_json
@dataclass
class Fields(SnipeDataObject):
    db_column_name: str = ""
    format: str = "ANY"
    field_values: str | None = None
    field_values_array: list[str] | None = None
    show_in_listview: bool = False
    type: str = ""
    required: bool = False
    display_in_user_view: bool = False
    auto_add_to_fieldsets: bool = False
    element: str = ""
    user_id: int | None = None
    field_encrypted: bool = False
    db_column: str = ""
    help_text: str = ""
    show_in_email: bool = False
    show_in_requestable_list: bool = False
    is_unique: bool = False
    pivot: dict = field(metadata=config(exclude=exclude_always), default_factory=dict)


@dataclass_json
@dataclass
class FieldSets(SnipeDataObject):
    # Fieldsets contains all the information about fields, but Models and Fields/Fieldsets are circular
    fields: list[dict] = field(metadata=config(exclude=exclude_always), default_factory=list)
    models: list[dict] = field(metadata=config(exclude=exclude_always), default_factory=list)
    user_id: int = field(metadata=config(exclude=exclude_always), default=0)

    def search(self, endpoint, payload=None, method='GET'):
        # FieldSet always return everything, so we need to handle that
        if not self.api:
            raise ValueError("API not set")
        if self.id:
            logging.debug("Already have an ID, no need to search")
            return self
        data = self.api.call('fieldsets', payload=None, method=method)
        if 'total' in data:
            for row in data['rows']:
                if row['name'] == self.name:
                    return self.populate(row, from_api=True)
        logging.debug(f"No matching fieldset found")
        return self


@dataclass
class Manufacturers(SnipeDataObject):
    url: str = field(metadata=config(exclude=exclude_ifempty), default="")
    image: str = field(metadata=config(exclude=exclude_always), default="")
    support_url: str = field(metadata=config(exclude=exclude_ifempty), default="")
    warranty_lookup_url: str = field(metadata=config(exclude=exclude_ifempty), default="")
    support_phone: str = field(metadata=config(exclude=exclude_ifempty), default="")
    support_email: str = field(metadata=config(exclude=exclude_ifempty), default="")
    assets_count: int = field(metadata=config(exclude=exclude_always), default=0)
    licenses_count: int = field(metadata=config(exclude=exclude_always), default=0)
    consumables_count: int = field(metadata=config(exclude=exclude_always), default=0)
    accessories_count: int = field(metadata=config(exclude=exclude_always), default=0)

    def __setattr__(self, key, value):
        if key == 'name':
            value = clean_manufacturer(value)
            if not value or len(value) < 4:
                # Manufacturers have to have at least 4 characters
                value = "Unknown"
        super().__setattr__(key, value)

    def get_by_name(self, name: str = ""):
        # Encode name with html entities
        name = html.escape(clean_manufacturer(name) or self.name)
        if not name or len(name) < 4:
            name = "Unknown"
        return self.search(f'manufacturers', payload={"name": name})


@dataclass
class Category(SnipeDataObject):
    image: str = field(metadata=config(exclude=exclude_always), default="")
    category_type: str = "asset"
    has_eula: bool = field(metadata=config(exclude=exclude_ifempty), default=False)
    use_default_eula: bool = True
    eula: str = field(metadata=config(exclude=exclude_always), default="")
    checkin_email: bool = False
    require_acceptance: bool = False
    item_count: int = field(metadata=config(exclude=exclude_always), default=0)
    assets_count: int = field(metadata=config(exclude=exclude_always), default=0)
    accessories_count: int = field(metadata=config(exclude=exclude_always), default=0)
    consumables_count: int = field(metadata=config(exclude=exclude_always), default=0)
    components_count: int = field(metadata=config(exclude=exclude_always), default=0)
    licenses_count: int = field(metadata=config(exclude=exclude_always), default=0)


@dataclass_json
@dataclass
class Models(SnipeDataObject):
    manufacturer: Manufacturers = field(metadata=config(exclude=exclude_always), default_factory=Manufacturers)
    manufacturer_id: int = 0
    image: str = field(metadata=config(exclude=exclude_always), default="")
    model_number: str = field(metadata=config(exclude=exclude_ifempty), default="")
    min_amt: int = field(metadata=config(exclude=exclude_always), default=0)
    depreciation: dict = field(metadata=config(exclude=exclude_always), default=dict)
    depreciation_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    assets_count: int = field(metadata=config(exclude=exclude_always), default=0)
    category: Category = field(metadata=config(exclude=exclude_always), default_factory=Category)
    category_id: int = 0
    fieldset: FieldSets = field(metadata=config(exclude=exclude_always), default_factory=FieldSets)
    fieldset_id: int = 0
    eol: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    deprecated_mac_address: int = field(metadata=config(exclude=exclude_always), default=0)
    notes: str = field(metadata=config(exclude=exclude_ifempty), default="")
    requestable: bool = field(metadata=config(exclude=exclude_always), default=True)

    def __setattr__(self, key, value):
        if key == 'name':
            value: str = clean_tag(value)
            if not value:
                value = "Unknown"
        if key == 'model_number':
            value: str = clean_tag(value)
            if not value:
                value = ""
        if key == 'eol':
            if not value or value == "None":
                value: int = 0
            if type(value) is str:
                value: int = int((value or "0").split(' ')[0])
        super().__setattr__(key, value)

    def get_by_name(self, name: str = "") -> Self:
        name = html.escape(clean_tag(name) or self.name)

        if not name:
            name = "Unknown"

        self.search('models', {"name": name})
        self.search('models', {"model_number": name})

        return self

    def get_by_model_number(self, model_number: str = "") -> Self:
        model_number_clean = html.escape(clean_tag(model_number) or self.model_number)

        if not model_number_clean:
            model_number_clean = "Unknown"

        self.search('models', {"model_number": model_number_clean})
        self.search('models', {"name": model_number_clean})

        return self


@dataclass_json
@dataclass
class StatusLabels(SnipeDataObject):
    type: str = "deployable"
    color: str | None = None
    show_in_nav: bool = False
    default_label: bool = True
    assets_count: int = field(metadata=config(exclude=exclude_always), default=0)
    notes: str = field(metadata=config(exclude=exclude_always), default="")
    status_type: str = field(metadata=config(exclude=exclude_always), default="")
    status_meta: dict = field(metadata=config(exclude=exclude_always), default_factory=dict)

    def __setattr__(self, name, value):
        if name == 'type':
            if value not in ['deployable', 'pending', 'archived', 'undeployable']:
                raise ValueError(f"Invalid status type: {value}")
        super().__setattr__(name, value)


@dataclass_json
@dataclass
class Groups(SnipeDataObject):
    notes: str = ""
    users_count: int = field(metadata=config(exclude=exclude_always), default=0)
    assets_count: int = field(metadata=config(exclude=exclude_always), default=0)
    licenses_count: int = field(metadata=config(exclude=exclude_always), default=0)
    accessories_count: int = field(metadata=config(exclude=exclude_always), default=0)
    consumables_count: int = field(metadata=config(exclude=exclude_always), default=0)


@dataclass_json
@dataclass
class Departments(SnipeDataObject):
    pass


@dataclass_json
@dataclass
class Locations(SnipeDataObject):
    image: str = field(metadata=config(exclude=exclude_ifempty), default="")
    address: str = ""
    address2: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    zip: str = ""
    phone: str = ""
    fax: str = ""
    assigned_assets_count: int = 0
    assets_count: int = 0
    rtd_assets_count: int = 0
    users_count: int = 0
    currency: str = ""
    ldap_ou: str = ""
    parent_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    parent: Locations | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    manager_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    manager: Users | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    # Children are of type Location, but we cannot infinitely recurse
    children: list[dict] = field(metadata=config(exclude=exclude_ifempty), default_factory=list)


@dataclass
class Suppliers(SnipeDataObject):
    # image: str
    # url: str
    # address: str
    # address2: str
    # city: str
    # state: str
    # country: str
    # zip_code: str
    # fax: str
    # phone: str
    # email: str
    # contact: str
    # assets_count: int
    # accessories_count: int
    # licenses_count: int
    # consumables_count: int
    # components_count: int
    # notes: str
    pass


@dataclass
class Company(SnipeObject):
    pass


@dataclass_json
@dataclass
class Users(SnipeDataObject):
    avatar: str = field(metadata=config(exclude=exclude_ifempty), default="")
    first_name: str = field(metadata=config(exclude=exclude_ifempty), default="")
    last_name: str = field(metadata=config(exclude=exclude_ifempty), default="")
    username: str = field(metadata=config(exclude=exclude_ifempty), default="")
    remote: bool = field(metadata=config(exclude=exclude_ifempty), default=False)
    locale: str = field(metadata=config(exclude=exclude_ifempty), default="")
    employee_num: str = field(metadata=config(exclude=exclude_ifempty), default="")
    manager: Users | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    manager_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    jobtitle: str = field(metadata=config(exclude=exclude_ifempty), default="")
    vip: bool = False
    phone: str = field(metadata=config(exclude=exclude_ifempty), default="")
    website: str = field(metadata=config(exclude=exclude_ifempty), default="")
    address: str = field(metadata=config(exclude=exclude_ifempty), default="")
    city: str = field(metadata=config(exclude=exclude_ifempty), default="")
    state: str = field(metadata=config(exclude=exclude_ifempty), default="")
    country: str = field(metadata=config(exclude=exclude_ifempty), default="")
    zip: str = field(metadata=config(exclude=exclude_ifempty), default="")
    email: str = field(metadata=config(exclude=exclude_ifempty), default="")
    department: Departments = field(metadata=config(exclude=exclude_ifempty), default_factory=Departments)
    department_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    location: Locations = field(metadata=config(exclude=exclude_ifempty), default_factory=Locations)
    notes: str = field(metadata=config(exclude=exclude_ifempty), default="")
    permissions: dict = field(metadata=config(exclude=exclude_ifempty), default_factory=dict)
    activated: bool = True
    autoassign_licenses: bool = field(metadata=config(exclude=exclude_always), default=False)
    ldap_import: bool = field(metadata=config(exclude=exclude_always), default=False)
    two_factor_enrolled: bool = False
    two_factor_optin: bool = False
    assets_count: int = field(metadata=config(exclude=exclude_always), default=0)
    licenses_count: int = field(metadata=config(exclude=exclude_always), default=0)
    accessories_count: int = field(metadata=config(exclude=exclude_always), default=0)
    consumables_count: int = field(metadata=config(exclude=exclude_always), default=0)
    company: Company = field(metadata=config(exclude=exclude_always), default_factory=Company)
    created_by: Users | None = field(metadata=config(exclude=exclude_always), default=None)
    start_date: str | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    end_date: str | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    last_login: str | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    # Groups contain Users and Users contain Groups, we cannot infinitely recurse
    groups: list[dict] | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    employee_number: str = field(metadata=config(exclude=exclude_ifempty), default="")
    type: str = field(metadata=config(exclude=exclude_ifempty), default="")

    def __setattr__(self, key, value):
        if key == 'username':
            value = clean_user(value)
        super().__setattr__(key, value)

    def get_by_username(self, username: str = "") -> Self:
        username = clean_user(username) if username else self.username
        return self.search(f'users', payload={"username": username})

    def get_by_employee_num(self, employee_num: str) -> Self:
        return self.search(f'users', payload={"employee_num": employee_num})


@dataclass_json
@dataclass
class Hardware(SnipeDataObject):
    asset_tag: str = ""
    status_id: int = 0
    model_id: int = 0
    # name
    # Optionals
    image: str = field(metadata=config(exclude=exclude_always), default="")  # TODO: This seems to want a file
    serial: str = field(metadata=config(exclude=exclude_ifempty), default=0)
    purchase_date: str | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    purchase_cost: float = field(metadata=config(exclude=exclude_ifempty), default=0)
    order_number: str = field(metadata=config(exclude=exclude_ifempty), default="")
    notes: str = field(metadata=config(exclude=exclude_ifempty), default="")
    archived: bool = field(metadata=config(exclude=exclude_ifempty), default=False)
    warranty_months: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    depreciate: bool = field(metadata=config(exclude=exclude_ifempty), default=False)
    supplier_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    requestable: bool = field(metadata=config(exclude=exclude_ifempty), default=False)
    rtd_location_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    last_audit_date: str | None = field(metadata=config(exclude=exclude_ifempty), default=None)
    location_id: int = field(metadata=config(exclude=exclude_ifempty), default=0)
    byod: bool = field(metadata=config(exclude=exclude_ifempty), default=False)
    # You shall not pass
    model: Models = field(metadata=config(exclude=exclude_always), default_factory=Models)
    status: StatusLabels = field(metadata=config(exclude=exclude_always), default_factory=StatusLabels)
    model_number: str = field(metadata=config(exclude=exclude_always), default="")
    # EOL gets calculated from the model
    eol: str | None = field(metadata=config(exclude=exclude_always), default=None)
    category: Category = field(metadata=config(exclude=exclude_always), default_factory=Category)
    category_id: int = field(metadata=config(exclude=exclude_always), default=0)
    manufacturer: Manufacturers = field(metadata=config(exclude=exclude_always), default_factory=Manufacturers)
    manufacturer_id: int = field(metadata=config(exclude=exclude_always), default=0)
    supplier: Suppliers = field(metadata=config(exclude=exclude_always), default_factory=Suppliers)
    company: Company = field(metadata=config(exclude=exclude_always), default_factory=Company)
    company_id: int = field(metadata=config(exclude=exclude_always), default=0)
    location: Locations = field(metadata=config(exclude=exclude_always), default_factory=Locations)
    rtd_location: Locations = field(metadata=config(exclude=exclude_always), default_factory=Locations)
    qr: str = field(metadata=config(exclude=exclude_always), default="")
    alt_barcode: str = field(metadata=config(exclude=exclude_always), default="")
    assigned_to: Users | int = field(metadata=config(exclude=exclude_always), default_factory=Users)
    warranty_expires: str | None = field(metadata=config(exclude=exclude_always), default=None)
    next_audit_date: str | None = field(metadata=config(exclude=exclude_always), default=None)
    age: str = field(metadata=config(exclude=exclude_always), default="")
    last_checkout: str | None = field(metadata=config(exclude=exclude_always), default=None)
    expected_checkin: str | None = field(metadata=config(exclude=exclude_always), default=None)
    checkin_counter: int = field(metadata=config(exclude=exclude_always), default=0)
    checkout_counter: int = field(metadata=config(exclude=exclude_always), default=0)
    requests_counter: int = field(metadata=config(exclude=exclude_always), default=0)
    user_can_checkout: bool = field(metadata=config(exclude=exclude_always), default=False)
    custom_fields: dict = field(metadata=config(exclude=exclude_always), default_factory=dict)
    available_actions: Actions = field(metadata=config(exclude=exclude_always), default_factory=Actions)

    def set_custom_field(self, human_name: str, value: str) -> Self:
        # This will trigger the custom_fields dict, see __setattr__
        setattr(self, self.custom_fields[human_name]['field'], value)
        return self

    def get_custom_field(self, human_name: str) -> str:
        return getattr(self, self.custom_fields[human_name]['field']) or ''

    def __setattr__(self, key, value: str | int | dict):
        logging.debug(f"Hardware: Setting {key} to {value} of type {type(value)}")

        if key == 'name':
            value: str = clean_tag(value).upper()
            if not value:
                value = self.asset_tag or self.serial or "Unknown"

        if key == 'asset_tag':
            value: str = clean_tag(value).upper()

        if key == 'serial':
            value: str = clean_tag(value).upper()

        if key == 'warranty_months' and type(value) is str:
            value: int = int((value or "0").split(' ')[0])

        if key == "custom_fields":
            for cfield_key, cfield_values in value.items():
                value[cfield_key]['value'] = html.unescape(cfield_values['value'])
                setattr(self, cfield_values['field'], cfield_values['value'])

        if key == "purchase_date" and value:
            if 'T' in value:
                # Snipe-IT returns date in ISO datetime format but expects them to be returned as strings %Y-%m-%d
                dt = parse_isoformat(value)
                value = dt.strftime("%Y-%m-%d")

        if key == "purchase_cost" and value:
            if type(value) is str:
                try:
                    value: float = float(re.sub(r'[^\d.]', '', value))
                except ValueError:
                    value = 0
            if type(value) is int:
                value: float = float(value)

        # Key starts with _snipeit_ and value is not empty and custom_fields is set
        if key.startswith('_snipeit_') and value and getattr(self, 'custom_fields', None):
            for cfield_key, cfield_values in self.custom_fields.items():
                if cfield_values['field'] == key:
                    if type(value) is str:
                        value = html.unescape(value)
                    self.custom_fields[cfield_key]['value'] = value
                    break

        super().__setattr__(key, value)

    def store_state(self):
        setattr(self, '_curr_data', self.to_dict() | self.get_custom_fields())
        return self

    def populate_mac(self, mac_addresses: list[str], remove_bad_vendor: bool = True):
        new_macs = []
        for mac in mac_addresses:
            new_mac = clean_mac(mac, remove_bad_vendor)
            new_macs.append(new_mac)

        new_macs = filter_list(new_macs)
        available_fields = []
        logging.debug(new_macs)
        for cf in self.custom_fields.values():
            if cf['field_format'] == 'MAC':
                if cf['value'] and cf['value'].upper() in new_macs:
                    # Remove the MAC address from the list
                    new_macs.remove(cf['value'].upper())
                if not cf['value']:
                    available_fields.append(cf['field'])

        for afield in available_fields:
            if new_macs:
                setattr(self, afield, new_macs.pop(0))

        return self

    def upsert(self, method='PATCH') -> Self:
        self.evaluate_edr()
        self.evaluate_last_user()
        extra_data = self.get_custom_fields()
        if not self.id:
            return self.create(extra_data=extra_data)

        curr_data = self.to_dict() | extra_data

        # If method is PATCH, we only want to update the fields that have changed
        if method == 'PATCH':
            curr_data = self.to_patch_dict(curr_data)

        if not curr_data:
            logging.debug("No changes to save")
            return self

        data = self.api.call(f"hardware/{self.id}", method=method, payload=curr_data)
        if "status" in data and data['status'] == "success" and "payload" in data and data['payload']:
            return self.populate(data['payload'], from_api=True)
        logging.debug(curr_data)
        raise ValueError(f"Failed to update hardware, {data}, {curr_data}")

    def get_custom_fields(self) -> dict[str, str]:
        custom_fields = {}

        if "custom_fields" not in self.__dict__:
            return custom_fields

        for cf in self.custom_fields.values():
            custom_fields[cf['field']] = cf['value']

        return custom_fields

    def get_by_name(self, name: str = "") -> Self:
        name = clean_tag(html.escape(name)).upper() or self.name or self.asset_tag or self.serial or "Unknown"
        if not name:
            logging.debug("Name not set")
            return self

        return self.search(f'hardware?filter={{"name":"{name}"}}')

    def get_by_mac(self, mac_addresses: list | None = None, remove_bad_vendors: bool = False) -> Self:
        if mac_addresses is None:
            mac_addresses = []

        fields_to_query = []
        # If we added MAC addresses some other way, then we want to also add them to the list
        for cf in self.custom_fields.values():
            if cf['field_format'] == 'MAC':
                fields_to_query.append(cf['field'])
                if cf['value']:
                    mac_addresses.append(cf['value'].upper())

        # Filter out empty and duplicates
        mac_addresses = filter_list(mac_addresses)

        for mac_address in mac_addresses:
            # Search implementation will return nothing on empty string
            if clean_mac(mac_address, remove_bad_vendors=remove_bad_vendors):
                for custom_field in fields_to_query:
                    self.search(f'hardware?filter={{"{custom_field}":"{mac_address}"}}')

        return self

    def get_by_asset_tag(self, asset_tag="") -> Self:
        asset_tag_clean = html.escape(clean_tag(asset_tag).upper() or self.asset_tag)
        if not asset_tag:
            logging.debug(f"No valid asset tag: {asset_tag}")
            return self

        return self.search(f"hardware/bytag/{asset_tag_clean}")

    def get_by_serial(self, serial="") -> Self:
        serial_clean = clean_tag(serial).upper() if serial else self.serial
        if not serial_clean:
            logging.debug(f"No valid serial number {serial}")
            return self

        return self.search(f"hardware/byserial/{serial_clean}")

    def checkout_to_user(self, user: Users, expected_checkin: str = "", checkout_at: str = "", note: str = "") -> Self:
        if not user.id:
            raise ValueError("User not found/created")
        if not self.id:
            raise ValueError("Hardware not created yet")
        if not note:
            note = f"From Snipe-IT API"

        if self.assigned_to and self.assigned_to.id == user.id:
            logging.debug(f"Already checked out to {self.assigned_to.username}")
            return self

        if self.assigned_to:
            logging.debug(f"Checking in {self.name} from {self.assigned_to.username}")
            self.checkin(note=note)

        payload = {
            'checkout_to_type': 'user',
            'assigned_user': user.id,
            'status_id': self.status_id,
            'name': self.name,
            'note': note
        }
        if expected_checkin:
            payload['expected_checkin'] = expected_checkin
        if checkout_at:
            payload['checkout_at'] = checkout_at
        data = self.api.call(f"hardware/{self.id}/checkout", method="POST", payload=payload)
        if not data['status'] == "success":
            raise ValueError(f"Failed to checkout {self.__class__.__name__}, {data}, {payload}")
        self.assigned_to = user
        return self

    def checkin(self, location_id: int = 0, note: str = ""):
        payload = {
            'note': note,
            'status_id': self.status_id,
            'name': self.name
        }
        if location_id:
            payload['location_id'] = location_id
        data = self.api.call(f"hardware/{self.id}/checkin", method="POST", payload=payload)
        if not data['status'] == "success":
            raise ValueError(f"Failed to checkin {self.__class__.__name__}, {data}, {payload}")
        return self

    def evaluate_edr(self) -> None:
        domain = self.get_custom_field('Domain')
        edr = self.get_custom_field('EDR')
        status = self.status_id
        ou = self.get_custom_field('Org. Unit').lower()
        # We are always deployed (SCCM)
        if status == DEFAULTS['status_id_pending'] and 'UR' in domain:
            self.status_id = DEFAULTS['status_id_deployed']
        if 'UR' in domain and 'research' in ou and "CrowdStrike Falcon" in edr:
            # 4 is Research (Compliant)
            self.status_id = 4
        elif 'research' in ou.lower():
            # 5 is Research (Non-Compliant)
            self.status_id = 5

    def evaluate_last_user(self) -> None:
        # Make sure to filter out the unknowns but maintain the domain
        last_user = clean_user(self.get_custom_field("Last User"))
        if not last_user:
            return

        if self.assigned_to and self.assigned_to.username.lower() == last_user.lower():
            return

        # Lookup the user
        user = Users(api=self.api, username=last_user).get_by_username()
        if not user.id:
            return
        if (user.department and user.department.name in DEFAULTS['techs']) or user.username in DEFAULTS['techs']:
            return

        # If we have an empty department, then update it
        if user.department and not self.get_custom_field("Department"):
            self.set_custom_field("Department", user.department.name)

        try:
            self.checkout_to_user(user)
        except ValueError:
            logging.error(f"Failed to check out {self.name} to {user.username}")
