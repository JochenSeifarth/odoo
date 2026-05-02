/** @odoo-module **/

/**
 * WhatsApp Floating Button JavaScript
 * Lightweight interaction handler for the WhatsApp button
 */

(function () {
      const whatsappBtn = document.getElementById('whatsapp_floating_btn');

      if (!whatsappBtn) {
            console.log('WhatsApp button not found in DOM');
            return;
      }

      console.log('WhatsApp button found, initializing...');

      // Get configuration from data attributes
      const config = {
            phone: whatsappBtn.dataset.phone || '',
            message: whatsappBtn.dataset.message || 'Hello',
            position: whatsappBtn.dataset.position || 'right',
            size: whatsappBtn.dataset.size || 'medium',
            tooltip: whatsappBtn.dataset.tooltip || 'Chat with us on WhatsApp'
      };

      console.log('WhatsApp config:', config);

      // Get the link element
      const link = whatsappBtn.querySelector('.whatsapp-link');
      if (!link) {
            console.log('WhatsApp link element not found');
            return;
      }

      // Create WhatsApp link
      if (config.phone) {
            // Clean phone number (remove spaces, dashes, parentheses, +)
            const cleanPhone = config.phone
                  .replace(/[\s\-\(\)]/g, '')
                  .replace(/^\+/, '');

            const encodedMessage = encodeURIComponent(config.message);
            const waLink = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;
            link.href = waLink;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';

            console.log('WhatsApp link created:', waLink);
      } else {
            console.log('No phone number configured, button will not open WhatsApp');
            link.href = '#';
            link.onclick = function (e) {
                  e.preventDefault();
                  alert('WhatsApp phone number not configured. Please configure it in Website Settings.');
                  return false;
            };
      }

      // Track click events (optional analytics)
      link.addEventListener('click', function (e) {
            // Dispatch custom event for analytics integration
            const event = new CustomEvent('whatsapp_button_click', {
                  detail: {
                        phone: config.phone,
                        message: config.message,
                        timestamp: new Date().toISOString()
                  }
            });
            document.dispatchEvent(event);

            console.log('WhatsApp button clicked');
      });


      // Add entrance animation
      whatsappBtn.style.opacity = '0';
      whatsappBtn.style.transform = 'scale(0.5)';

      setTimeout(function () {
            whatsappBtn.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            whatsappBtn.style.opacity = '1';
            whatsappBtn.style.transform = 'scale(1)';
      }, 300);

      console.log('WhatsApp floating button initialized successfully');
})();
