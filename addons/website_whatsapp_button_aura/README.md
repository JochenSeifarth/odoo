# Website Floating WhatsApp Button

A lightweight Odoo 19 module that adds a floating WhatsApp chat button to your website.

## Features

✅ **Floating WhatsApp Button** - Displays on all website pages  
✅ **Click to Chat** - Opens WhatsApp with pre-filled message  
✅ **Dynamic Configuration** - Set phone number and default message  
✅ **Position Control** - Place button on left or right side  
✅ **Size Options** - Small, Medium, or Large button  
✅ **ON/OFF Toggle** - Enable or disable from Website Settings  
✅ **Super Lightweight** - Pure CSS + JS, no heavy dependencies  
✅ **Mobile Responsive** - Adapts to all screen sizes  
✅ **Pulse Animation** - Eye-catching attention grabber  
✅ **Tooltip on Hover** - Customizable hover text

## Installation

1. Copy the `website_whatsapp_button_aura` folder to your Odoo addons directory
2. Update the app list: `Apps > Update Apps List`
3. Search for "WhatsApp" and install the module

## Configuration

1. Go to **Website > Configuration > Settings**
2. Scroll to **WhatsApp Button** section
3. Enable the button
4. Configure:
   - **Phone Number**: Your WhatsApp number with country code (e.g., +1234567890)
   - **Default Message**: Pre-filled message for visitors
   - **Position**: Left or Right side of the screen
   - **Size**: Small (50px), Medium (60px), or Large (70px)
   - **Tooltip Text**: Text shown on hover

## Screenshots

### Button on Website

The floating button appears in the corner of your website, with a smooth pulse animation.

### Settings Page

Easy configuration from the Website Settings panel.

## Technical Details

- **Odoo Version**: 19.0
- **Dependencies**: `website`
- **License**: LGPL-3

### File Structure

```
website_whatsapp_button_aura/
├── __init__.py
├── __manifest__.py
├── README.md
├── controllers/
│   ├── __init__.py
│   └── main.py
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py
│   └── website.py
├── security/
│   └── ir.model.access.csv
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── css/
│       │   └── whatsapp_button.css
│       └── js/
│           └── whatsapp_button.js
└── views/
    ├── res_config_settings_views.xml
    └── website_whatsapp_templates.xml
```

## Customization

### CSS Variables

You can customize the button appearance by overriding CSS in your theme:

```css
/* Change button color */
.whatsapp-float .whatsapp-link {
  background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
}

/* Change position offset */
.whatsapp-float {
  bottom: 30px;
}
.whatsapp-float.whatsapp-right {
  right: 30px;
}
```

### Disable Pulse Animation

Add to your custom CSS:

```css
.whatsapp-float .whatsapp-link::before {
  animation: none;
}
```

## Support

For issues or feature requests, please contact us.

## License

This module is licensed under LGPL-3.
