/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// Convert decimal degrees to D°M′N/S or D°M′E/W
function decimalToDMS(decimal, isLat) {
    if (decimal == null) return "";
    const deg = Math.floor(Math.abs(decimal));
    const min = (Math.abs(decimal) - deg) * 60;
    const dir = isLat ? (decimal >= 0 ? " N" : " S") : (decimal >= 0 ? " E" : " W");
    return `${deg}°${min.toFixed(1)}′${dir}`;
}

// Base field component
class CoordinateField extends Component {
    static props = { ...standardFieldProps };
    get value() {
        // Modern Odoo 19: the field value is in props.record.data[field.name]
        return this.props.record?.data?.[this.props.name] ?? null;
    }
}

// Latitude
class LatitudeDMSField extends CoordinateField {
    static template = xml`
      <span>
        <t t-esc="displayValue"/>
      </span>
    `;
    get displayValue() {
        return decimalToDMS(this.value, true);
    }
}

// Longitude
class LongitudeDMSField extends CoordinateField {
    static template = xml`
      <span>
        <t t-esc="displayValue"/>
      </span>
    `;
    get displayValue() {
        return decimalToDMS(this.value, false);
    }
}

// Register widgets
registry.category("fields").add("latitude_dms", {
    component: LatitudeDMSField,
    supportedTypes: ["float"],
});
registry.category("fields").add("longitude_dms", {
    component: LongitudeDMSField,
    supportedTypes: ["float"],
});